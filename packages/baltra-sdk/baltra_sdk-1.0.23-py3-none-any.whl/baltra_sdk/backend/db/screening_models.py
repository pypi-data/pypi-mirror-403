# from app import db
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy import Index, CheckConstraint, text, create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import NullPool

db = SQLAlchemy()


def build_db_url_from_settings(settings) -> str:
    """Build database URL from settings object."""
    return (
        f"postgresql+psycopg2://{settings.DB_USER}:{settings.DB_PASSWORD}"
        f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    )


class DBShim:
    """
    Database session manager for lambdas and non-Flask contexts.
    Allows using Flask-SQLAlchemy models with explicit sessions.
    """
    def __init__(self, db_url: str):
        """
        Initialize DBShim with a database URL.
        
        Args:
            db_url: PostgreSQL connection string
        """
        self.engine = create_engine(
            db_url,
            poolclass=NullPool,
            future=True,
        )
        self._SessionFactory = sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
            future=True,
        )
        self.Session = scoped_session(self._SessionFactory)
        
        # Bind Flask-SQLAlchemy models metadata to this engine
        # This allows using db.Model classes with explicit sessions
        db.Model.metadata.bind = self.engine

    @classmethod
    def from_settings(cls, settings) -> "DBShim":
        """Create DBShim from settings object."""
        return cls(build_db_url_from_settings(settings))

    @property
    def session(self):
        """Get a new database session."""
        return self.Session()

    def remove_session(self):
        """Remove the current session from the scoped session registry."""
        self.Session.remove()

ResponseTypeEnum = db.Enum(
    'text', 'location', 'voice', 'phone_reference', 'interactive', 'name', 'location_critical', 
    name='response_type_enum', 
    create_type=False
)
CompanyScreeningGroupLogicEnum = db.Enum(
    'BUSINESS_UNIT', 
    'ROLES', 
    name='company_screening_group_logic_enum', 
    create_type=False
)
UserPermissionEnum = db.Enum(
    'ENABLE_BILLING_TAB',
    'ENABLE_BUSINESS_UNIT_EDIT_TAB',
    'ENABLE_INTERVIEWED_CANDIDATES_EDIT_TAB',
    name='user_permission_enum',
    create_type=False
)

# TODO
# 1. Create a table to define what we show in the dashboard for each user and company group [DONE]
# 2. Expand CompanyGroups attributes [PENDING]
# 3. Define where we will define which funnel states require a business unit [PENDING]


class Users(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    cognito_sub = db.Column(db.String(255), unique=True, nullable=False, index=True)

    last_login_at = db.Column(db.DateTime(timezone=True), nullable=True)
    notify_interviews_email_enabled = db.Column(db.Boolean, nullable=False, default=True)
    notify_pulse_weekly_email_enabled = db.Column(db.Boolean, nullable=False, default=True)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    permissions = db.Column(db.ARRAY(UserPermissionEnum), nullable=True)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.text("now()"))
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.text("now()"), onupdate=db.text("now()"))

    company_group_ids = db.Column(db.JSON, nullable=True) 
    business_unit_ids = db.Column(db.JSON, nullable=True)

    def __repr__(self):
        return f'<User {self.id} {self.email}>'


# Company Information Tables
class CompanyGroups(db.Model):
    __tablename__ = "company_groups"

    company_group_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    website = db.Column(db.Text)
    wa_id = db.Column(db.String(50))
    phone = db.Column(db.String(50))

    company_screening_group_logic = db.Column(CompanyScreeningGroupLogicEnum)
    
    __table_args__ = (
        db.Index("idx_company_groups_name", "name"),
    )
    

class BusinessUnits(db.Model):
    __tablename__ = "business_units"

    # General Business Unit Information
    business_unit_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    # NOTE: latitude, longitude, address, hr_contact, interview_address_json, maps_link_json
    # have been moved to Roles table and Locations table.
    # Access location info via: Roles.location_id -> Locations (for work location)
    # Access interview location via: Roles.location_id_interview -> Locations (for interview location)
    # Access hr_contact via: Roles.hr_contact
    # 
    # default_location_id: Fallback location when role doesn't have a location or no role is specified.
    # This is the primary fallback before querying any location for the business unit.
    default_location_id = db.Column(db.Integer, db.ForeignKey("locations.location_id", ondelete="SET NULL"), nullable=True)
    website = db.Column(db.Text) 
    benefits = db.Column(MutableList.as_mutable(db.JSON), default=list) # PENDING: move to roles table
    general_faq = db.Column(db.JSON)   # TODO: Define General FAQ Structure - what it will include
    
    phone = db.Column(db.String)

    funnel_states_business_unit = db.Column(db.JSON) # ['Pendientes', 'Confirmados', 'No contestaron']

    #Todo: DELETE ONE OF THESE TWO
    description = db.Column(db.Text)
    additional_info = db.Column(db.Text)
    
    # Interview Information
    interview_excluded_dates = db.Column(MutableList.as_mutable(db.JSON), default=list)
    interview_days = db.Column(MutableList.as_mutable(db.JSON), default=list)
    interview_hours = db.Column(MutableList.as_mutable(db.JSON), default=list)
    max_interviews_per_slot = db.Column(db.Integer, nullable=True)
    

    # Assistant Information
    classifier_assistant_id = db.Column(db.String)
    general_purpose_assistant_id = db.Column(db.String)
    ad_trigger_phrase = db.Column(db.Text)
    reminder_schedule = db.Column(db.JSON, nullable=False, default=dict)
    customer_id = db.Column(db.String(50))
    timezone = db.Column(db.String(50), nullable=False, server_default=text("'America/Mexico_City'"), default="America/Mexico_City")
    qr_attendance_s3_path = db.Column(db.String(500), nullable=True)
    referral_options = db.Column(
        db.JSON,
        nullable=True,
        server_default=text("""'["Facebook","Flyer","Manta de la Empresa","Referido","Otra"]'""")
    )
    maximum_location_km = db.Column(db.Float, nullable=True, server_default=db.text("30.0"), default=30.0)
    
    # Meta Business Information
    wa_id = db.Column(db.String)
    company_is_verified_by_meta = db.Column(db.Boolean, nullable=False, server_default=db.text("true"), default=True)

    # Company Group Information
    company_group_id = db.Column(db.Integer, db.ForeignKey("company_groups.company_group_id", ondelete="SET NULL"))

    # Relationship for default location
    default_location = db.relationship("Locations", foreign_keys=[default_location_id], backref="default_for_business_units")

    __table_args__ = (
        CheckConstraint("char_length(description) <= 250", name="description_length_check"),
        db.Index("idx_business_units_default_location", "default_location_id"),
    )


class ProductUsage(db.Model):
    __tablename__ = "product_usage"
    
    product_usage_id = db.Column(db.Integer, primary_key=True)
    business_unit_id = db.Column(db.Integer, db.ForeignKey('business_units.business_unit_id', ondelete="CASCADE"), nullable=False)
    
    # Feature flags for product usage
    eligibility = db.Column(db.Boolean, nullable=False, default=False)
    phone_interviews = db.Column(db.Boolean, nullable=False, default=False)
    qr_code = db.Column(db.Boolean, nullable=False, default=False)
    employee_onboarding = db.Column(db.Boolean, nullable=False, default=False)
    
    # Relationship
    business_unit = db.relationship("BusinessUnits", backref="product_usage")


class DashboardConfigurations(db.Model):
    __tablename__ = "dashboard_configurations"

    dashboard_configuration_id = db.Column(db.Integer, primary_key=True)
    funnel_states_baltra = db.Column(db.JSON) # ['Evaluados', 'Citados', 'Entrevistados', 'Contratados', 'Ingresados']
    
    show_lastest_ad_campaigns = db.Column(db.Boolean, nullable=False, default=True)
    show_hiring_volume = db.Column(db.Boolean, nullable=False, default=True)
    show_phone_interview_information = db.Column(db.Boolean, nullable=False, default=True)
    show_onboarding_tab = db.Column(db.Boolean, nullable=False, default=True)
    show_business_unit_profile_tab = db.Column(db.Boolean, nullable=False, default=True)

    interviewed_candidates_keys = db.Column(db.JSON)

    # DashboardConfiguration.interview_candidate_keys = {
    #     "Estado": "estado",
    #     "Es zurdo": "es_zurdo",
    #     "Cualquier opcion": "cualquier_opcion"
    # }

    business_unit_id = db.Column(db.Integer, db.ForeignKey('business_units.business_unit_id', ondelete="CASCADE"), nullable=False)


class HiringObjectives(db.Model):
    __tablename__ = "hiring_objectives"

    hiring_objective_id = db.Column(db.Integer, primary_key=True)
    company_group_id = db.Column(db.Integer, db.ForeignKey('company_groups.company_group_id', ondelete="CASCADE"), nullable=False) 
    business_unit_id = db.Column(db.Integer, db.ForeignKey('business_units.business_unit_id', ondelete="CASCADE"), nullable=False)
    
    role_id = db.Column(db.Integer, db.ForeignKey('roles.role_id', ondelete="CASCADE"), nullable=False)
    objective_amount = db.Column(db.Integer, nullable=False)

    objective_type = db.Column(db.Text, nullable=False)
    objective_name = db.Column(db.Text, nullable=False)
    objective_duration = db.Column(db.Date, nullable=False)
    objective_period_year = db.Column(db.Integer, nullable=False)
    objective_period_month = db.Column(db.Integer, nullable=False)
    objective_created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.text("now()"))


class Roles(db.Model):
    __tablename__ = 'roles'

    role_id = db.Column(db.Integer, primary_key=True)
    business_unit_id = db.Column(db.Integer, db.ForeignKey('business_units.business_unit_id', ondelete="CASCADE"), nullable=False)
    role_name = db.Column(db.Text, nullable=False)
    # role_description: Plain text description of the role
    role_description = db.Column(db.Text)
    # role_info: JSON containing FAQ Q&A pairs in format { "Q1": "...", "A1": "...", "Q2": "...", "A2": "...", ... }
    role_info = db.Column(db.JSON)
    is_active = db.Column(db.Boolean, default=True)
    set_id = db.Column(db.Integer, db.ForeignKey('question_sets.set_id', ondelete="SET NULL"))
    eligibility_criteria = db.Column(db.JSON)
    default_role = db.Column(db.Boolean, default=False)
    is_deleted = db.Column(db.Boolean, default=False)
    # role_list_subtitle: Subtitle shown in WhatsApp list messages when candidates select a role (max 72 chars)
    # NOTE: This was renamed from 'shift' column. The old 'shift' was being used for list subtitles.
    role_list_subtitle = db.Column(db.Text)
    # shift: Actual shift/schedule information for the role (e.g., "Lunes a Viernes 8am-5pm")
    shift = db.Column(db.Text)
    location_id = db.Column(db.Integer, db.ForeignKey("locations.location_id", ondelete="SET NULL"))
    location_id_interview = db.Column(db.Integer, db.ForeignKey("locations.location_id", ondelete="SET NULL"))
    hr_contact = db.Column(db.Text)  # HR contact information for this role
    
    # Role-specific requirements and information
    document_requirements = db.Column(db.JSON)  # List of required documents for this role
    transport_pdf_link = db.Column(db.Text)  # Link to transport/commute PDF for this role
    
    # Compensation structure: { "banco": str, "neto_bruto": str, "salario": number, "bonos": number, "frecuencia": str}
    compensation = db.Column(db.JSON)
    
    # Age requirements: { "min": number, "max": number }
    edades = db.Column(db.JSON)
    
    # Education level requirements: { "primaria": bool, "secundaria": bool, "preparatoria": bool, "preparatoria_tecnica": bool, "licenciatura": bool }
    education_level = db.Column(db.JSON)
    
    additional_faqs = db.Column(db.JSON)  # Role-specific FAQs
    
    # Relationships for location access
    location = db.relationship("Locations", foreign_keys=[location_id], backref="roles_work")
    location_interview = db.relationship("Locations", foreign_keys=[location_id_interview], backref="roles_interview")

    __table_args__ = (
        CheckConstraint("char_length(role_name) <= 24", name="role_name_length_check"),
        CheckConstraint("char_length(role_list_subtitle) <= 72", name="role_list_subtitle_length_check"), 
    )
    
class Locations(db.Model):
    __tablename__ = 'locations'

    location_id = db.Column(db.Integer, primary_key=True)
    business_unit_id = db.Column(db.Integer, db.ForeignKey('business_units.business_unit_id', ondelete='CASCADE'), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    url = db.Column(db.Text)
    address = db.Column(db.Text)

    # Relationships
    # NOTE: foreign_keys is required because BusinessUnits also has default_location_id FK to Locations
    # Without it, SQLAlchemy can't determine which FK path to use for the join
    business_unit = db.relationship("BusinessUnits", foreign_keys=[business_unit_id], backref="locations")

    # Constraints
    __table_args__ = (
        db.CheckConstraint('latitude BETWEEN -90 AND 90', name='check_valid_latitude'),
        db.CheckConstraint('longitude BETWEEN -180 AND 180', name='check_valid_longitude'),
        db.Index('idx_locations_business_unit', 'business_unit_id'),
    )



# Candidate Information Tables
class Candidates(db.Model):
    __tablename__ = "candidates"

    candidate_id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(30), nullable=False)
    name = db.Column(db.Text)
    age = db.Column(db.Integer)
    gender = db.Column(db.Text)
    education_level = db.Column(db.Text)
    source = db.Column(db.Text)
    referred_by = db.Column(db.Text, nullable=True, server_default="Baltra", default="Baltra")
    grade = db.Column(db.Integer)
    funnel_state = db.Column(db.Text)
    funnel_state_business_unit = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.text("now()"))
    start_date = db.Column(db.Date)


    interview_date_time = db.Column(db.DateTime(timezone=True))
    interview_reminder_sent = db.Column(db.Boolean, nullable=False, default=False)
    interview_address = db.Column(db.Text)
    interview_map_link = db.Column(db.Text)
    interview_confirmed = db.Column(db.Boolean, default=None)

    interviewed_candidates_keys = db.Column(db.JSON, nullable=True)
    # Candidates.interview_candidate_keys = {
    #     "estado": "Entrevistado",
    #     "es_zurdo": "Es zurdo",
    #     "cualquier_opcion": "..."
    # }

    
    travel_time_minutes = db.Column(db.Integer, server_default='0')
    application_reminder_sent = db.Column(db.Boolean, default=False)
    flow_state = db.Column(db.String(50), nullable=False, server_default="respuesta")
    eligible_roles = db.Column(db.JSON)
    reschedule_sent = db.Column(db.Boolean, default=False)
    rejected_reason = db.Column(db.Text)
    screening_rejected_reason = db.Column(db.Text)
    end_flow_rejected = db.Column(db.Boolean, nullable=False, default=False)
    worked_here = db.Column(db.Boolean, nullable=True) 
    eligible_companies = db.Column(db.JSON, nullable=True)
    appointment_reminder_counters = db.Column(db.JSON, nullable=True, default=lambda: {"phone_call_count": 0, "message_count": 0})
    coordinates_json = db.Column(db.JSON, nullable=True)

    # Specific Business Unit Attributes
    especific_business_unit_attributes = db.Column(db.JSON, nullable=True)

    # Relationships
    company_group_id = db.Column(db.Integer, db.ForeignKey("company_groups.company_group_id"), nullable=True)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.role_id", ondelete="SET NULL"))
    business_unit_id = db.Column(db.Integer, db.ForeignKey("business_units.business_unit_id", ondelete="CASCADE"))
    

    __table_args__ = (
        db.PrimaryKeyConstraint('candidate_id', name='candidates_pkey1'),
        db.Index('idx_candidates_company_group_id', 'company_group_id'),
        db.Index('idx_candidates_business_unit_id', 'business_unit_id'),
        db.Index('idx_candidates_company_group_name', 'company_group_id', 'name'),
        db.Index('idx_candidates_capacity_check', 'business_unit_id', 'interview_date_time', 'funnel_state'),  # For capacity checking performance
        # Optional functional index for case-insensitive prefix searches (requires migration support in production)
        # db.Index('idx_candidates_company_lower_name', db.text('company_group_id'), db.text('lower(name)')),
    )

class CandidateFunnelLog(db.Model):
    __tablename__ = 'candidate_funnel_logs'

    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.candidate_id', ondelete='CASCADE'), nullable=False)
    previous_funnel_state = db.Column(db.Text)
    new_funnel_state = db.Column(db.Text, nullable=False)
    changed_at = db.Column(db.DateTime, nullable=False, server_default=db.text("CURRENT_TIMESTAMP"))

    # Relationship to Candidate
    candidate = db.relationship("Candidates", backref="funnel_logs")

    __table_args__ = (
        db.Index('candidate_funnel_candidate_id_idx', 'candidate_id'),
        db.Index('candidate_funnel_new_funnel_state_idx', 'new_funnel_state'),
        db.Index('idx_cfl_candidate_changed', 'candidate_id', db.text('changed_at DESC')),
        db.Index('idx_cfl_changed_at', 'changed_at'),
        db.Index('idx_cfl_prev_new_changed', 'previous_funnel_state', 'new_funnel_state', 'changed_at'),
        db.Index('idx_cfl_new_state', 'new_funnel_state'),
    )




# Candidate Interaction Guides Tables
class QuestionSets(db.Model):
    __tablename__ = "question_sets"

    set_id = db.Column(db.Integer, primary_key=True)
    business_unit_id = db.Column(db.Integer, db.ForeignKey("business_units.business_unit_id", ondelete="CASCADE"), nullable=True)
    set_name = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.text("now()"))
    general_set = db.Column(db.Boolean, nullable=False, default=False)
    group_id = db.Column(db.Integer, db.ForeignKey("company_groups.company_group_id", ondelete="CASCADE"),nullable=True)

    business_unit = db.relationship("BusinessUnits", backref="question_sets")
    group = db.relationship("CompanyGroups", backref="question_sets")
    screening_questions = db.relationship("ScreeningQuestions", backref="question_set", cascade="all, delete-orphan")
    __table_args__ = (
        Index(
            'one_general_set_per_business_unit',
            'business_unit_id',
            'group_id',
            unique=True,
            postgresql_where=db.text('general_set IS TRUE')
        ),
        db.CheckConstraint(
            "(business_unit_id IS NOT NULL AND group_id IS NULL) OR "
            "(business_unit_id IS NULL AND group_id IS NOT NULL)",
            name="business_unit_or_group"
        ),
    )

class ScreeningQuestions(db.Model):
    __tablename__ = "screening_questions"

    question_id = db.Column(db.Integer, primary_key=True)
    set_id = db.Column(db.Integer, db.ForeignKey("question_sets.set_id", ondelete="CASCADE"), nullable=False)
    position = db.Column(db.SmallInteger, nullable=False)
    question = db.Column(db.Text, nullable=False)
    response_type = db.Column(ResponseTypeEnum, nullable=False)
    question_metadata = db.Column(db.JSON)
    end_interview_answer = db.Column(db.Text)
    example_answer = db.Column(db.Text)
    is_blocked = db.Column(db.Boolean, default=False)
    eligibility_question = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    # Relationships
    screening_answers = db.relationship("ScreeningAnswers", backref="question", cascade="all, delete-orphan")

    __table_args__ = (
        db.UniqueConstraint('set_id', 'position', name='screening_questions_set_id_position_key'),
        db.Index('idx_questions_set_pos', 'set_id', 'position')
    )

class ScreeningAnswers(db.Model):
    __tablename__ = "screening_answers"

    answer_id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey("candidates.candidate_id", ondelete="CASCADE"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("screening_questions.question_id", ondelete="CASCADE"), nullable=False)
    answer_raw = db.Column(db.Text)
    answer_json = db.Column(db.JSON)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.text("now()"))

    __table_args__ = (
        db.UniqueConstraint('candidate_id', 'question_id', name='screening_answers_candidate_id_question_id_key'),
        db.Index('idx_answers_candidate', 'candidate_id'),
        db.Index('idx_answers_question', 'question_id')
    )

class MessageTemplates(db.Model):
    __tablename__ = 'message_templates'

    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.Text, nullable=False)
    button_trigger = db.Column(db.Text)
    type = db.Column(db.Text, nullable=False)
    text = db.Column(db.Text)
    interactive_type = db.Column(db.Text)
    button_keys = db.Column(db.JSON)
    footer_text = db.Column(db.Text)
    header_type = db.Column(db.Text)
    header_content = db.Column(db.Text)
    parameters = db.Column(db.JSON)
    template = db.Column(db.Text)
    variables = db.Column(db.JSON)
    url_keys = db.Column(db.JSON)
    header_base = db.Column(db.Text)
    flow_keys = db.Column(db.JSON)
    flow_action_data = db.Column(db.JSON)
    document_link = db.Column(db.Text)  # renamed from 'link'
    filename = db.Column(db.Text)
    flow_name = db.Column(db.Text)
    flow_cta = db.Column(db.Text)
    list_options = db.Column(db.JSON)             # [{"id": "opt_1", "title": "Sí", "description": "Confirmar asistencia"}]
    list_section_title = db.Column(db.Text)  
    display_name = db.Column(db.Text)
    business_unit_id = db.Column(db.Integer, db.ForeignKey('business_units.business_unit_id', ondelete="CASCADE"))
    
    business_unit = db.relationship("BusinessUnits", backref="message_templates")

class PhoneInterviewQuestions(db.Model):
    __tablename__ = 'phone_interview_questions'

    id = db.Column(db.Integer, primary_key=True)
    business_unit_id = db.Column(db.Integer, db.ForeignKey('business_units.business_unit_id', ondelete='CASCADE'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.role_id', ondelete='SET NULL'))
    question_text = db.Column(db.Text, nullable=False)
    position = db.Column(db.SmallInteger, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.text('now()'))
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.text('now()'))

    # Relationships
    business_unit = db.relationship('BusinessUnits', backref='phone_interview_questions')
    role = db.relationship('Roles', backref='phone_interview_questions')

    __table_args__ = (
        db.Index('idx_phone_q_business_unit_role_pos', 'business_unit_id', 'role_id', 'position'),
        db.Index('idx_phone_q_business_unit', 'business_unit_id'),
    )



# Candidate Interaction History Tables
class PhoneInterviews(db.Model):
    __tablename__ = "phone_interviews"

    interview_id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey("candidates.candidate_id", ondelete="CASCADE"), nullable=False)
    business_unit_id = db.Column(db.Integer, db.ForeignKey("business_units.business_unit_id", ondelete="CASCADE"), nullable=False)
    elevenlabs_call_id = db.Column(db.String(255), unique=True, nullable=False)
    call_status = db.Column(db.String(50), nullable=False)  # 'completed', 'failed', 'missed', 'scheduled'
    call_duration = db.Column(db.Integer)  # in seconds
    started_at = db.Column(db.DateTime(timezone=True))
    ended_at = db.Column(db.DateTime(timezone=True))
    transcript = db.Column(db.Text)
    summary = db.Column(db.Text)
    ai_score = db.Column(db.Integer)  # AI-generated interview score (1-100)
    ai_recommendation = db.Column(db.String(50))  # 'recommended', 'not_recommended', 'pending_review'
    thread_id_openai = db.Column(db.String(255))  # OpenAI thread ID used for transcript evaluation
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.text("now()"))
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.text("now()"))

    # Relationships
    candidate = db.relationship("Candidates", backref="phone_interviews")
    business_unit = db.relationship("BusinessUnits", backref="phone_interviews")

    __table_args__ = (
        db.Index('idx_phone_interviews_candidate', 'candidate_id'),
        db.Index('idx_phone_interviews_business_unit', 'business_unit_id'),
        db.Index('idx_phone_interviews_vapi_call', 'elevenlabs_call_id'),
        db.Index('idx_phone_interviews_status', 'call_status'),
    )

    def __repr__(self):
        return f'<PhoneInterview {self.interview_id}: candidate_id={self.candidate_id}, status={self.call_status}>'

class WhatsappStatusUpdates(db.Model):
    __tablename__ = 'whatsapp_status_updates'

    id = db.Column(db.Integer, primary_key=True)
    object_type = db.Column(db.String(50))
    entry_id = db.Column(db.BigInteger)
    messaging_product = db.Column(db.String(50))
    wa_id = db.Column(db.String(15))
    phone_number_id = db.Column(db.String(50))
    message_body = db.Column(db.Text)
    conversation_id = db.Column(db.String(50))
    origin_type = db.Column(db.String(50))
    billable = db.Column(db.Boolean)
    pricing_model = db.Column(db.String(50))
    category = db.Column(db.String(50))
    status = db.Column(db.String(20))
    timestamp = db.Column(db.BigInteger)
    field = db.Column(db.String(50))
    status_id = db.Column(db.String(100))
    lag_killed = db.Column(db.Boolean, default=False)
    campaign_id = db.Column(db.String(100))
    error_info = db.Column(db.JSON)

class ScreeningMessages(db.Model):
    __tablename__ = 'screening_messages'
    message_serial = db.Column(db.Integer, primary_key=True)
    wa_id = db.Column(db.String(50))
    business_unit_id = db.Column(db.Integer, db.ForeignKey('business_units.business_unit_id'))
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.candidate_id'))
    message_id = db.Column(db.String(50))
    thread_id = db.Column(db.String(50))
    time_stamp = db.Column(db.DateTime)
    sent_by = db.Column(db.String(50))
    message_body = db.Column(db.Text)
    conversation_type = db.Column(db.String(10))
    whatsapp_msg_id = db.Column(db.String(100))
    set_id = db.Column(db.Integer, db.ForeignKey('question_sets.set_id'))
    question_id = db.Column(db.Integer, db.ForeignKey('screening_questions.question_id'))

    # Relationships
    business_unit = db.relationship("BusinessUnits", backref="screening_messages")
    candidate = db.relationship("Candidates", backref="screening_messages")
    question = db.relationship("ScreeningQuestions", backref="screening_messages")

class CandidateReferences(db.Model):
    __tablename__ = "candidate_references"

    reference_id = db.Column(db.Integer, primary_key=True)
    reference_wa_id = db.Column(db.String(50))
    candidate_id = db.Column(db.Integer, db.ForeignKey("candidates.candidate_id", ondelete="CASCADE"), nullable=False)
    set_id = db.Column(db.Integer, db.ForeignKey("question_sets.set_id", ondelete="CASCADE"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("screening_questions.question_id", ondelete="CASCADE"), nullable=False)
    reach_out_delivered = db.Column(db.Boolean, default=False)
    reference_complete = db.Column(db.Boolean, default=False)
    assessment = db.Column(db.JSON)

    candidate = db.relationship("Candidates", backref="candidate_references", lazy="joined")

class ReferenceMessages(db.Model):
    __tablename__ = "reference_messages"

    message_serial = db.Column(db.Integer, primary_key=True)
    wa_id = db.Column(db.String(50))
    reference_id = db.Column(
        db.Integer,
        db.ForeignKey("candidate_references.reference_id", ondelete="CASCADE")
    )
    message_id = db.Column(db.String(50))
    thread_id = db.Column(db.String(50))
    time_stamp = db.Column(db.DateTime)
    sent_by = db.Column(db.String(50))
    message_body = db.Column(db.Text)
    conversation_type = db.Column(db.String(10))
    whatsapp_msg_id = db.Column(db.String(100))

class CandidateMedia(db.Model):
    __tablename__ = "candidate_media"

    media_id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey("candidates.candidate_id", ondelete="CASCADE"))
    business_unit_id = db.Column(db.Integer, db.ForeignKey("business_units.business_unit_id", ondelete="CASCADE"))
    question_id = db.Column(db.Integer, db.ForeignKey("screening_questions.question_id", ondelete="SET NULL"))
    set_id = db.Column(db.Integer)
    string_submission = db.Column(db.Text)
    media_type = db.Column(db.String(50))  # 'image', 'document', 'text', etc.
    media_subtype = db.Column(db.String(50))  # 'INE', 'RFC', 'CURP', etc.
    file_name = db.Column(db.String(255))
    mime_type = db.Column(db.String(100))
    file_size = db.Column(db.Integer)
    s3_bucket = db.Column(db.String(100))
    s3_key = db.Column(db.String(500))
    s3_url = db.Column(db.String(1000))
    upload_timestamp = db.Column(db.DateTime, server_default=db.text("CURRENT_TIMESTAMP"))
    whatsapp_media_id = db.Column(db.String(100))
    sha256_hash = db.Column(db.String(100))
    flow_token = db.Column(db.String(100))
    verified = db.Column(db.Boolean, default=False)
    verification_result = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, server_default=db.text("CURRENT_TIMESTAMP"))
    updated_at = db.Column(db.DateTime, server_default=db.text("CURRENT_TIMESTAMP"))

    __table_args__ = (
        db.Index('idx_candidate_media_candidate_id', 'candidate_id'),
        db.Index('idx_candidate_media_business_unit_id', 'business_unit_id'),
        db.Index('idx_candidate_media_question_id', 'question_id'),
        db.Index('idx_candidate_media_upload_timestamp', 'upload_timestamp'),
        db.Index('idx_candidate_media_whatsapp_id', 'whatsapp_media_id'),
        db.Index('idx_candidate_media_business_unit_subtype_string', 'business_unit_id', 'media_subtype', 'string_submission'),
    )

class OnboardingResponses(db.Model):
    __tablename__ = "onboarding_responses"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey("candidates.candidate_id", ondelete="CASCADE"), nullable=True, index=True)
    business_unit_id = db.Column(db.Integer, db.ForeignKey("business_units.business_unit_id", ondelete="SET NULL"), nullable=True, index=True)
    company_group_id = db.Column(db.Integer, db.ForeignKey("company_groups.company_group_id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    question = db.Column(db.Text, nullable=True)
    answer = db.Column(db.Text, nullable=True)
    survey = db.Column(db.String, nullable=True)

    candidate = db.relationship("Candidates", backref="onboarding_responses")
    business_unit = db.relationship("BusinessUnits", backref="onboarding_responses")
    company_group = db.relationship("CompanyGroups", backref="onboarding_responses")

    __table_args__ = (
        db.Index('idx_onboarding_responses_candidate_id', 'candidate_id'),
        db.Index('idx_onboarding_responses_business_unit_id', 'business_unit_id'),
        db.Index('idx_onboarding_responses_company_group_id', 'company_group_id'),
    )


class EmailLogs(db.Model):
    __tablename__ = "email_logs"

    id = db.Column(db.BigInteger, primary_key=True)
    recipient_email = db.Column(db.String(320), nullable=False)
    business_unit_id = db.Column(db.Integer, db.ForeignKey('business_units.business_unit_id', ondelete="SET NULL"), nullable=True)
    subject = db.Column(db.Text, nullable=True)
    template_name = db.Column(db.String(150), nullable=True)
    payload = db.Column(db.JSON, nullable=True)
    message_id = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), nullable=False, default="sent")
    error_info = db.Column(db.Text, nullable=True)
    sent_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)

    # Relationships
    business_unit = db.relationship("BusinessUnits", backref="email_logs")

    __table_args__ = (
        db.Index("idx_email_logs_recipient", "recipient_email"),
        db.Index("idx_email_logs_business_unit", "business_unit_id"),
        db.Index("idx_email_logs_sent_at", "sent_at"),
    )


# Performance Tracking Tables
class ResponseTiming(db.Model):
    __tablename__ = 'response_timings'

    id = db.Column(db.Integer, primary_key=True)  # Clave primaria
    employee_id = db.Column(db.Integer, nullable=False)
    business_unit_id = db.Column(db.Integer, db.ForeignKey('business_units.business_unit_id', ondelete="CASCADE"), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    time_delta = db.Column(db.Numeric, nullable=False)
    assistant_id = db.Column(db.String(50))
    # Token and model usage fields
    model = db.Column(db.String(50), nullable=False)
    prompt_tokens = db.Column(db.Integer, nullable=False)
    completion_tokens = db.Column(db.Integer, nullable=False)
    total_tokens = db.Column(db.Integer, nullable=False)

    # Relationships
    business_unit = db.relationship("BusinessUnits", backref="response_timings")

class EligibilityEvaluationLog(db.Model):
    __tablename__ = 'eligibility_evaluation_log'
    
    evaluation_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.candidate_id'), nullable=False, index=True)
    business_unit_id = db.Column(db.Integer, db.ForeignKey('business_units.business_unit_id', ondelete='CASCADE'), nullable=False, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.role_id'), nullable=False, index=True)
    role_name = db.Column(db.String(255), nullable=False)
    
    # AI evaluation result
    is_eligible = db.Column(db.Boolean, nullable=False)
    ai_reasoning = db.Column(db.Text, nullable=True)  # The "reasoning" field from AI response
    raw_ai_response = db.Column(db.JSON, nullable=True)  # Full JSON response from AI
    
    # Questions and answers used for evaluation  
    questions_and_answers = db.Column(db.JSON, nullable=True)  # The input data used
    eligibility_criteria = db.Column(db.JSON, nullable=True)  # Role criteria used
    
    # Manual review fields
    manual_review_status = db.Column(db.String(50), nullable=True, index=True)  # null, 'pending', 'reviewed'
    manual_review_result = db.Column(db.Boolean, nullable=True)  # Manual verification: True/False/null
    manual_review_date = db.Column(db.DateTime, nullable=True)
    
    # Metadata
    evaluation_date = db.Column(db.DateTime, nullable=False, default=db.func.now())
    assistant_id = db.Column(db.String(100), nullable=True)  # OpenAI assistant ID used
    thread_id = db.Column(db.String(100), nullable=True)  # OpenAI thread ID
    
    # Relationships
    candidate = db.relationship('Candidates', backref='eligibility_evaluations')
    role = db.relationship('Roles', backref='eligibility_evaluations')
    business_unit = db.relationship('BusinessUnits', backref='eligibility_evaluations')
    
    def __repr__(self):
        return f'<EligibilityLog {self.evaluation_id}: candidate_id={self.candidate_id}, role_id={self.role_id}, eligible={self.is_eligible}>'




# Whatever else we need to add


class AdTemplate(db.Model):
    __tablename__ = 'ad_templates'

    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(db.String(50), nullable=False)
    key = db.Column(db.String(255), nullable=False, unique=True)
    json_data = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.text("now()"))

    def __repr__(self):
        return f'<AdTemplate {self.id} {self.key}>'


class ScreeningConversationStatus(db.Model):
    __tablename__ = "screening_conversation_status"

    id = db.Column(db.SmallInteger, primary_key=True)
    code = db.Column(db.String(32), nullable=False, unique=True)
    description = db.Column(db.Text)

    conversations = db.relationship("ScreeningConversation", back_populates="status")


class ScreeningConversation(db.Model):
    __tablename__ = "screening_conversation"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    wa_phone_id = db.Column(db.String(32), nullable=False)
    user_phone = db.Column(db.String(32), nullable=False)
    status_id = db.Column(
        db.SmallInteger,
        db.ForeignKey("screening_conversation_status.id", ondelete="RESTRICT"),
        nullable=False,
        server_default=text("1"),
    )
    status_changed_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    last_webhook_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    active_run_id = db.Column(db.String(64))
    active_thread_id = db.Column(db.String(64))
    active_run_priority = db.Column(db.String(32))
    cancel_requested = db.Column(db.Boolean, nullable=False, server_default=text("false"))

    status = db.relationship("ScreeningConversationStatus", back_populates="conversations")
    temp_messages = db.relationship("TempMessage", back_populates="conversation", cascade="all, delete-orphan")

    __table_args__ = (
        db.UniqueConstraint("wa_phone_id", "user_phone", name="uq_screening_conversation_wa_phone_user_phone"),
        db.Index("idx_screening_conversation_status_changed", "status_id", "status_changed_at"),
        db.Index("idx_screening_conversation_last_webhook", "last_webhook_at"),
    )


class WaMessageType(db.Model):
    __tablename__ = "wa_message_type"

    id = db.Column(db.SmallInteger, primary_key=True)
    code = db.Column(db.String(32), nullable=False, unique=True)


class WaInteractiveType(db.Model):
    __tablename__ = "wa_interactive_type"

    id = db.Column(db.SmallInteger, primary_key=True)
    code = db.Column(db.String(32), nullable=False, unique=True)


class TempMessage(db.Model):
    __tablename__ = "temp_messages"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    conversation_id = db.Column(
        db.BigInteger,
        db.ForeignKey("screening_conversation.id", ondelete="CASCADE"),
        nullable=False,
    )
    message_id = db.Column(db.String(255))
    wa_id = db.Column(db.String(255))
    body = db.Column(db.JSON)
    received_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    processing = db.Column(db.Boolean, nullable=False, server_default=text("FALSE"))
    wa_type = db.Column(db.String(32))
    wa_interactive_type = db.Column(db.String(32))
    wa_type_id = db.Column(
        db.SmallInteger,
        db.ForeignKey("wa_message_type.id", ondelete="RESTRICT"),
        nullable=True,
    )
    wa_interactive_type_id = db.Column(
        db.SmallInteger,
        db.ForeignKey("wa_interactive_type.id", ondelete="RESTRICT"),
        nullable=True,
    )
    openai_message_id = db.Column(db.String(64))

    conversation = db.relationship("ScreeningConversation", back_populates="temp_messages")

    __table_args__ = (
        db.Index("idx_temp_messages_conversation_processing", "conversation_id", "processing"),
    )


@event.listens_for(DashboardConfigurations, 'before_insert')
@event.listens_for(DashboardConfigurations, 'before_update')
def ensure_estado_in_interviewed_candidates_keys(mapper, connection, target):
    """Ensure 'Estado': 'estado' is always present in interviewed_candidates_keys"""
    if target.interviewed_candidates_keys is None:
        target.interviewed_candidates_keys = {}
    
    if not isinstance(target.interviewed_candidates_keys, dict):
        target.interviewed_candidates_keys = {}
    
    if "Estado" not in target.interviewed_candidates_keys:
        target.interviewed_candidates_keys = {
            "Estado": "estado",
            **target.interviewed_candidates_keys
        }


@event.listens_for(Candidates, 'before_insert')
@event.listens_for(Candidates, 'before_update')
def ensure_estado_in_candidate_interviewed_keys(mapper, connection, target):
    """Ensure 'estado' is always present in interviewed_candidates_keys with funnel_state value"""
    if target.interviewed_candidates_keys is None:
        target.interviewed_candidates_keys = {}
    
    if not isinstance(target.interviewed_candidates_keys, dict):
        target.interviewed_candidates_keys = {}
    
    estado_value = target.funnel_state if target.funnel_state else ""
    target.interviewed_candidates_keys["estado"] = estado_value


class MetaTestResult(db.Model):
    __tablename__ = "meta_test_results"

    meta_test_result_id = db.Column(db.BigInteger, primary_key=True)
    direction = db.Column(db.String, nullable=False)
    wa_phone_id = db.Column(db.String)
    wa_id_user = db.Column(db.String)
    payload = db.Column(db.JSON)
    payload_text = db.Column(db.Text)
    test_round_id = db.Column(db.BigInteger)
    test_round_fullname = db.Column(db.Text)
    test_round_business_unit_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
