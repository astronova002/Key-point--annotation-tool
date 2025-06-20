# Database Schema Documentation
## Keypoint Annotation Tool for Infant Pose Detection

### Schema Overview
This database schema is specifically designed for medical-grade keypoint annotation workflows, supporting the creation of high-quality infant pose detection datasets for cerebral palsy research and custom YOLO model training.

### Design Principles
1. **Medical Compliance**: Structured for healthcare data requirements
2. **Quality Control**: Multi-stage verification and approval processes
3. **Scalability**: Supports large-scale annotation projects
4. **Modularity**: Configurable for different keypoint schemas and ML models
5. **Auditability**: Complete tracking of all user actions and data changes
6. **Performance**: Optimized indexing for high-volume operations

## Core Entities

### 1. User (Authentication & Role Management)
```sql
User {
    -- Identity & Authentication
    id: bigint PRIMARY KEY,
    username: varchar(150) UNIQUE NOT NULL,
    email: varchar(254) UNIQUE NOT NULL,
    password: varchar(128) NOT NULL,
    
    -- Role-based Access Control
    role: enum('ADMIN', 'ANNOTATOR', 'VERIFIER') NOT NULL,
    is_approved: boolean DEFAULT false,
    is_active: boolean DEFAULT true,
    is_staff: boolean DEFAULT false,
    is_superuser: boolean DEFAULT false,
    
    -- Role-specific Configuration
    max_concurrent_batches: integer DEFAULT 2,  -- For annotators
    annotation_specialty: varchar(100) NULL,    -- Focus area (e.g., "upper_body", "full_body")
    verification_expertise: varchar(100) NULL,  -- For verifiers (e.g., "pediatric_physiotherapy")
    
    -- Performance Tracking
    total_annotations_completed: integer DEFAULT 0,
    total_verifications_completed: integer DEFAULT 0,
    avg_annotation_time_minutes: decimal(5,2) DEFAULT 0.00,
    accuracy_score: decimal(3,2) DEFAULT 0.00,  -- 0.00 to 1.00
    
    -- Audit Fields
    date_joined: timestamp DEFAULT NOW(),
    last_login: timestamp NULL,
    created_by: bigint REFERENCES User(id) NULL,
    
    -- Indexes
    INDEX idx_user_role_approved (role, is_approved),
    INDEX idx_user_email (email),
    INDEX idx_user_active (is_active)
}
```

**Business Rules:**
- Only ADMIN users can approve new registrations
- ANNOTATOR and VERIFIER roles require admin approval
- max_concurrent_batches prevents annotator overload
- accuracy_score calculated from verification feedback

### 2. KeypointSchema (Configurable Annotation Structure)
```sql
KeypointSchema {
    id: bigint PRIMARY KEY,
    name: varchar(100) UNIQUE NOT NULL,           -- "infant-pose-17", "medical-skeleton-25"
    version: varchar(10) NOT NULL,                -- "v1.0", "v2.1"
    description: text NULL,
    
    -- Schema Definition (JSON structure)
    schema_definition: json NOT NULL,             -- Keypoint names, connections, colors
    total_keypoints: integer NOT NULL,
    required_keypoints: json NULL,                -- Minimum required for valid annotation
    
    -- Validation Rules
    min_visibility_threshold: decimal(2,1) DEFAULT 0.5,
    max_missing_keypoints: integer DEFAULT 3,
    
    -- Status & Metadata
    is_active: boolean DEFAULT true,
    created_by: bigint REFERENCES User(id) NOT NULL,
    created_at: timestamp DEFAULT NOW(),
    last_modified: timestamp DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_keypoint_schema_active (is_active),
    INDEX idx_keypoint_schema_name (name)
}
```

**Schema Definition Example:**
```json
{
  "keypoints": [
    {"id": 0, "name": "nose", "color": "#FF0000", "required": true},
    {"id": 1, "name": "left_eye", "color": "#00FF00", "required": true},
    {"id": 2, "name": "right_eye", "color": "#0000FF", "required": true},
    {"id": 5, "name": "left_shoulder", "color": "#FFFF00", "required": true},
    {"id": 6, "name": "right_shoulder", "color": "#FF00FF", "required": true}
  ],
  "connections": [[0,1], [0,2], [5,6]],  -- Skeleton connections for visualization
  "body_parts": {
    "head": [0,1,2],
    "torso": [5,6,11,12],
    "arms": [5,7,9,6,8,10],
    "legs": [11,13,15,12,14,16]
  }
}
```

### 3. ImageBatch (Organized Image Management)
```sql
ImageBatch {
    id: bigint PRIMARY KEY,
    batch_name: varchar(255) NOT NULL,
    description: text NULL,
    
    -- Configuration
    keypoint_schema_id: bigint REFERENCES KeypointSchema(id) NOT NULL,
    total_images: integer NOT NULL,
    
    -- Processing Status
    status: enum('UPLOADED', 'YOLO_PROCESSING', 'YOLO_COMPLETED', 'READY_FOR_ANNOTATION', 'ASSIGNED', 'IN_PROGRESS', 'COMPLETED', 'ARCHIVED') DEFAULT 'UPLOADED',
    
    -- YOLO Processing Metrics
    yolo_processing_started: timestamp NULL,
    yolo_processing_completed: timestamp NULL,
    yolo_model_version: varchar(20) NULL,
    avg_yolo_confidence: decimal(3,2) NULL,
    failed_yolo_count: integer DEFAULT 0,
    
    -- Quality Control
    quality_check_passed: boolean DEFAULT false,
    min_image_quality_score: decimal(2,1) DEFAULT 7.0,  -- 1-10 scale
    
    -- Metadata
    upload_metadata: json NULL,                    -- Source info, session details
    processing_priority: integer DEFAULT 5,        -- 1-10, higher = more urgent
    
    -- Ownership & Timing
    uploaded_by: bigint REFERENCES User(id) NOT NULL,
    uploaded_at: timestamp DEFAULT NOW(),
    
    -- Progress Tracking
    assigned_count: integer DEFAULT 0,
    completed_count: integer DEFAULT 0,
    approved_count: integer DEFAULT 0,
    rejected_count: integer DEFAULT 0,
    
    -- Indexes
    INDEX idx_batch_status (status),
    INDEX idx_batch_uploaded_by (uploaded_by),
    INDEX idx_batch_schema (keypoint_schema_id),
    INDEX idx_batch_priority (processing_priority, uploaded_at)
}
```

### 4. Image (Core Content Entity)
```sql
Image {
    id: bigint PRIMARY KEY,
    batch_id: bigint REFERENCES ImageBatch(id) NOT NULL,
    
    -- File Information
    filename: varchar(255) NOT NULL,
    original_filename: varchar(255) NOT NULL,
    storage_path: varchar(500) NOT NULL,
    thumbnail_path: varchar(500) NULL,
    
    -- Image Properties
    width: integer NOT NULL,
    height: integer NOT NULL,
    file_size: bigint NOT NULL,
    mime_type: varchar(50) NOT NULL,
    format: varchar(10) NOT NULL,                  -- 'JPEG', 'PNG'
    
    -- Medical/Research Metadata
    infant_metadata: json NULL,                    -- age_months, gender, session_type
    acquisition_date: date NULL,
    source_institution: varchar(100) NULL,
    anonymization_status: boolean DEFAULT false,
    
    -- YOLO Processing Results
    yolo_keypoints: json NULL,                     -- Initial AI detection coordinates
    yolo_confidence: decimal(3,2) NULL,
    yolo_processing_time_ms: integer NULL,
    yolo_model_version: varchar(20) NULL,
    
    -- Quality Assessment
    image_quality_score: decimal(2,1) NULL,        -- 1-10 scale
    has_quality_issues: boolean DEFAULT false,
    quality_issues: json NULL,                     -- ["blur", "poor_lighting", "occlusion"]
    
    -- Workflow Status
    status: enum('UPLOADED', 'YOLO_PROCESSED', 'ASSIGNED', 'IN_PROGRESS', 'ANNOTATED', 'SUBMITTED', 'UNDER_REVIEW', 'APPROVED', 'REJECTED', 'REQUIRES_REVISION') DEFAULT 'UPLOADED',
    
    -- Assignment Tracking
    current_annotator: bigint REFERENCES User(id) NULL,
    current_verifier: bigint REFERENCES User(id) NULL,
    
    -- Flags
    is_difficult_case: boolean DEFAULT false,
    requires_specialist_review: boolean DEFAULT false,
    has_annotation_issues: boolean DEFAULT false,
    
    -- Timing
    created_at: timestamp DEFAULT NOW(),
    last_status_change: timestamp DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_image_batch_status (batch_id, status),
    INDEX idx_image_status (status),
    INDEX idx_image_annotator (current_annotator),
    INDEX idx_image_quality (image_quality_score),
    INDEX idx_image_created (created_at)
}
```

### 5. BatchAssignment (Task Management)
```sql
BatchAssignment {
    id: bigint PRIMARY KEY,
    batch_id: bigint REFERENCES ImageBatch(id) NOT NULL,
    annotator_id: bigint REFERENCES User(id) NOT NULL,
    assigned_by: bigint REFERENCES User(id) NOT NULL,
    
    -- Assignment Configuration
    assignment_type: enum('INITIAL', 'REVISION', 'QUALITY_CHECK', 'SECOND_OPINION') DEFAULT 'INITIAL',
    priority: integer DEFAULT 5,                   -- 1-10
    special_instructions: text NULL,
    estimated_completion_hours: integer NULL,
    
    -- Status & Progress
    status: enum('ASSIGNED', 'ACKNOWLEDGED', 'IN_PROGRESS', 'COMPLETED', 'SUBMITTED', 'OVERDUE') DEFAULT 'ASSIGNED',
    progress_percentage: decimal(5,2) DEFAULT 0.00,
    images_completed: integer DEFAULT 0,
    images_total: integer NOT NULL,
    
    -- Timing
    assigned_at: timestamp DEFAULT NOW(),
    acknowledged_at: timestamp NULL,              -- When annotator starts work
    due_date: timestamp NULL,
    started_at: timestamp NULL,
    completed_at: timestamp NULL,
    
    -- Performance Tracking
    total_time_spent_minutes: integer DEFAULT 0,
    avg_time_per_image_minutes: decimal(5,2) DEFAULT 0.00,
    pause_count: integer DEFAULT 0,
    
    -- Quality Metrics
    self_reported_difficulty: integer NULL,        -- 1-5 scale
    completion_confidence: decimal(3,2) NULL,      -- Annotator's confidence in work
    
    -- Indexes
    INDEX idx_assignment_annotator_status (annotator_id, status),
    INDEX idx_assignment_batch (batch_id),
    INDEX idx_assignment_due_date (due_date),
    INDEX idx_assignment_assigned_at (assigned_at)
}
```

### 6. Annotation (Core Output Entity)
```sql
Annotation {
    id: bigint PRIMARY KEY,
    image_id: bigint REFERENCES Image(id) NOT NULL,
    batch_assignment_id: bigint REFERENCES BatchAssignment(id) NOT NULL,
    
    -- Keypoint Data (Primary Output)
    refined_keypoints: json NOT NULL,              -- Final annotator coordinates
    keypoint_confidence: json NULL,                -- Per-keypoint confidence 0-1
    keypoint_visibility: json NULL,                -- Per-keypoint visibility flags
    keypoint_notes: json NULL,                     -- Per-keypoint specific notes
    
    -- Quality & Difficulty Assessment
    annotation_quality_score: decimal(3,2) NULL,  -- Self-assessment 0-1
    difficulty_rating: enum('EASY', 'MEDIUM', 'HARD', 'VERY_HARD') NULL,
    difficulty_reasons: json NULL,                 -- ["blur", "unusual_pose", "occlusion"]
    
    -- Technical Metadata
    annotation_tool_version: varchar(20) NULL,
    total_keypoints_modified: integer DEFAULT 0,   -- From YOLO baseline
    major_corrections_made: boolean DEFAULT false,
    used_ai_suggestions: boolean DEFAULT false,
    
    -- Annotator Feedback
    general_notes: text NULL,
    image_quality_feedback: text NULL,
    suggested_improvements: text NULL,
    
    -- Versioning & Revision
    version: integer DEFAULT 1,
    is_revision: boolean DEFAULT false,
    original_annotation_id: bigint REFERENCES Annotation(id) NULL,
    revision_reason: text NULL,
    
    -- Performance Data
    time_spent_seconds: integer NOT NULL,
    pause_count: integer DEFAULT 0,
    zoom_level_used: decimal(3,1) NULL,
    
    -- Status & Timing
    status: enum('DRAFT', 'COMPLETED', 'SUBMITTED', 'UNDER_REVIEW', 'APPROVED', 'REVISION_REQUESTED') DEFAULT 'DRAFT',
    created_at: timestamp DEFAULT NOW(),
    updated_at: timestamp DEFAULT NOW(),
    submitted_at: timestamp NULL,
    
    -- Indexes
    INDEX idx_annotation_image (image_id),
    INDEX idx_annotation_assignment (batch_assignment_id),
    INDEX idx_annotation_status (status),
    INDEX idx_annotation_submitted (submitted_at),
    INDEX idx_annotation_quality (annotation_quality_score)
}
```

**Keypoint Data Structure Example:**
```json
{
  "keypoints": [
    {"id": 0, "name": "nose", "x": 245.5, "y": 123.2, "confidence": 0.95, "visible": 1},
    {"id": 1, "name": "left_eye", "x": 235.1, "y": 118.7, "confidence": 0.88, "visible": 1},
    {"id": 2, "name": "right_eye", "x": 255.3, "y": 119.1, "confidence": 0.92, "visible": 1}
  ],
  "modifications_from_yolo": {
    "total_moved": 12,
    "major_changes": [0, 5, 6],  -- Keypoint IDs with significant corrections
    "avg_displacement": 15.3     -- Average pixels moved
  }
}
```

### 7. Verification (Quality Control Entity)
```sql
Verification {
    id: bigint PRIMARY KEY,
    annotation_id: bigint REFERENCES Annotation(id) NOT NULL,
    verifier_id: bigint REFERENCES User(id) NOT NULL,
    
    -- Verification Decision
    decision: enum('APPROVED', 'APPROVED_WITH_CORRECTIONS', 'MINOR_REVISION_NEEDED', 'MAJOR_REVISION_NEEDED', 'REJECTED') NOT NULL,
    
    -- Corrections & Feedback
    corrected_keypoints: json NULL,                -- Verifier's corrections
    correction_summary: text NULL,
    detailed_feedback: text NULL,
    feedback_to_annotator: text NULL,              -- Constructive feedback
    internal_notes: text NULL,                     -- For admin/research use
    
    -- Quality Assessment
    overall_quality_score: integer NOT NULL,       -- 1-10 scale
    anatomical_accuracy: integer NULL,             -- 1-10 scale
    technical_precision: integer NULL,             -- 1-10 scale
    completeness_score: integer NULL,              -- 1-10 scale
    
    -- Specific Quality Metrics
    keypoint_accuracy_scores: json NULL,           -- Per-keypoint accuracy assessment
    problematic_keypoints: json NULL,              -- List of keypoint IDs with issues
    
    -- Rejection Handling
    rejection_reason: enum('POOR_IMAGE_QUALITY', 'INCORRECT_KEYPOINTS', 'ANATOMICAL_ERRORS', 'INCOMPLETE_ANNOTATION', 'TECHNICAL_ISSUES', 'GUIDELINES_VIOLATION', 'OTHER') NULL,
    rejection_details: text NULL,
    can_be_reannotated: boolean DEFAULT true,
    requires_specialist_input: boolean DEFAULT false,
    
    -- Medical/Clinical Assessment (if applicable)
    clinical_relevance: enum('HIGH', 'MEDIUM', 'LOW') NULL,
    diagnostic_quality: enum('EXCELLENT', 'GOOD', 'ADEQUATE', 'POOR') NULL,
    research_usability: boolean DEFAULT true,
    
    -- Performance Tracking
    verification_time_seconds: integer NOT NULL,
    complexity_rating: integer NULL,               -- 1-5, how difficult to verify
    certainty_level: integer NOT NULL,             -- 1-10, verifier's confidence
    
    -- Workflow
    is_final_decision: boolean DEFAULT true,
    requires_second_opinion: boolean DEFAULT false,
    escalated_to_admin: boolean DEFAULT false,
    
    -- Timing
    verified_at: timestamp DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_verification_annotation (annotation_id),
    INDEX idx_verification_verifier (verifier_id),
    INDEX idx_verification_decision (decision),
    INDEX idx_verification_quality (overall_quality_score),
    INDEX idx_verification_date (verified_at)
}
```

### 8. MLModelConfig (Modular Model Management)
```sql
MLModelConfig {
    id: bigint PRIMARY KEY,
    model_name: varchar(100) NOT NULL,             -- "yolo-v8-pose", "custom-infant-detector"
    version: varchar(20) NOT NULL,                 -- "1.0", "2.1-beta"
    model_type: enum('YOLO', 'DETECTRON', 'CUSTOM') NOT NULL,
    
    -- Schema Compatibility
    keypoint_schema_id: bigint REFERENCES KeypointSchema(id) NOT NULL,
    supports_confidence_scores: boolean DEFAULT true,
    supports_visibility_flags: boolean DEFAULT true,
    
    -- Model Configuration
    model_parameters: json NOT NULL,               -- Confidence thresholds, NMS settings
    input_resolution: json NOT NULL,               -- {"width": 640, "height": 640}
    preprocessing_config: json NULL,               -- Normalization, augmentation settings
    
    -- Performance Metrics
    avg_processing_time_ms: integer NULL,
    avg_confidence_score: decimal(3,2) NULL,
    success_rate: decimal(3,2) NULL,
    
    -- Deployment Info
    model_path: varchar(500) NULL,
    api_endpoint: varchar(500) NULL,
    deployment_status: enum('DEVELOPMENT', 'TESTING', 'PRODUCTION', 'DEPRECATED') DEFAULT 'DEVELOPMENT',
    
    -- Status & Metadata
    is_active: boolean DEFAULT true,
    description: text NULL,
    training_dataset_info: text NULL,
    
    -- Ownership & Timing
    created_by: bigint REFERENCES User(id) NOT NULL,
    created_at: timestamp DEFAULT NOW(),
    last_updated: timestamp DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_ml_model_active (is_active),
    INDEX idx_ml_model_type (model_type),
    INDEX idx_ml_model_schema (keypoint_schema_id)
}
```

### 9. AuditLog (Comprehensive Activity Tracking)
```sql
AuditLog {
    id: bigint PRIMARY KEY,
    
    -- User & Action Info
    user_id: bigint REFERENCES User(id) NULL,
    action: varchar(100) NOT NULL,                 -- 'BATCH_CREATED', 'ANNOTATION_SUBMITTED', etc.
    action_category: enum('USER_MANAGEMENT', 'IMAGE_PROCESSING', 'ANNOTATION', 'VERIFICATION', 'SYSTEM') NOT NULL,
    
    -- Resource Information
    resource_type: varchar(50) NOT NULL,           -- 'Image', 'Annotation', 'Batch', 'User'
    resource_id: bigint NOT NULL,
    resource_name: varchar(255) NULL,
    
    -- Change Details
    old_values: json NULL,                         -- Before state
    new_values: json NULL,                         -- After state
    change_summary: text NULL,
    
    -- Context Information
    session_id: varchar(100) NULL,
    ip_address: inet NOT NULL,
    user_agent: text NULL,
    api_endpoint: varchar(200) NULL,
    request_method: varchar(10) NULL,
    
    -- Performance Metrics
    action_duration_ms: integer NULL,
    processing_time_ms: integer NULL,
    
    -- Status & Results
    status: enum('SUCCESS', 'FAILED', 'PARTIAL') DEFAULT 'SUCCESS',
    error_message: text NULL,
    warning_messages: json NULL,
    
    -- Additional Context
    batch_context: json NULL,                      -- Related batch information
    annotation_context: json NULL,                 -- Related annotation details
    system_context: json NULL,                     -- System state, versions, etc.
    
    -- Timing
    created_at: timestamp DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_audit_user_action (user_id, action),
    INDEX idx_audit_resource (resource_type, resource_id),
    INDEX idx_audit_created (created_at),
    INDEX idx_audit_action_category (action_category),
    INDEX idx_audit_status (status)
}
```

### 10. PerformanceMetrics (Analytics & Reporting)
```sql
PerformanceMetrics {
    id: bigint PRIMARY KEY,
    user_id: bigint REFERENCES User(id) NOT NULL,
    
    -- Time Period
    metrics_date: date NOT NULL,
    period_type: enum('DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY') NOT NULL,
    period_start: timestamp NOT NULL,
    period_end: timestamp NOT NULL,
    
    -- Annotation Metrics (for annotators)
    images_annotated: integer DEFAULT 0,
    annotations_created: integer DEFAULT 0,
    annotations_revised: integer DEFAULT 0,
    avg_time_per_annotation_minutes: decimal(5,2) DEFAULT 0.00,
    total_annotation_time_minutes: integer DEFAULT 0,
    
    -- Verification Metrics (for verifiers)
    annotations_verified: integer DEFAULT 0,
    annotations_approved: integer DEFAULT 0,
    annotations_rejected: integer DEFAULT 0,
    avg_verification_time_minutes: decimal(5,2) DEFAULT 0.00,
    
    -- Quality Metrics
    accuracy_score: decimal(3,2) DEFAULT 0.00,     -- Overall accuracy
    avg_quality_rating: decimal(3,2) DEFAULT 0.00,
    improvement_trend: decimal(3,2) DEFAULT 0.00,   -- Week-over-week improvement
    
    -- Efficiency Metrics
    productivity_score: decimal(3,2) DEFAULT 0.00,
    consistency_score: decimal(3,2) DEFAULT 0.00,
    learning_curve_indicator: decimal(3,2) DEFAULT 0.00,
    
    -- Detailed Statistics
    keypoint_accuracy_breakdown: json NULL,        -- Per-keypoint accuracy stats
    difficulty_distribution: json NULL,            -- Easy/Medium/Hard distribution
    time_distribution: json NULL,                  -- Time spent patterns
    error_patterns: json NULL,                     -- Common mistake types
    
    -- Comparative Metrics
    peer_comparison_percentile: integer NULL,      -- 1-100 percentile among peers
    improvement_rate: decimal(5,2) DEFAULT 0.00,   -- Rate of improvement
    
    -- System Performance (for admins)
    system_uptime_percentage: decimal(5,2) NULL,
    avg_processing_time_ms: integer NULL,
    error_rate_percentage: decimal(5,2) NULL,
    
    -- Calculation Metadata
    calculated_at: timestamp DEFAULT NOW(),
    calculation_version: varchar(10) DEFAULT '1.0',
    data_completeness: decimal(3,2) DEFAULT 1.00,  -- How complete the source data was
    
    -- Indexes
    INDEX idx_performance_user_date (user_id, metrics_date),
    INDEX idx_performance_period (period_type, period_start),
    INDEX idx_performance_accuracy (accuracy_score),
    UNIQUE INDEX idx_performance_unique (user_id, metrics_date, period_type)
}
```

## Relationships & Constraints

### Primary Relationships
1. **User → ImageBatch**: One user uploads many batches
2. **ImageBatch → Image**: One batch contains many images
3. **ImageBatch → BatchAssignment**: One batch assigned to one annotator
4. **BatchAssignment → Annotation**: One assignment produces many annotations
5. **Annotation → Verification**: One annotation gets one verification
6. **KeypointSchema → ImageBatch**: Schema defines annotation structure

### Key Constraints
1. **Referential Integrity**: All foreign keys enforced
2. **Status Transitions**: Controlled through application logic
3. **Role Permissions**: Database-level role checks where applicable
4. **Data Consistency**: Triggers for maintaining counts and metrics

### Performance Optimizations
1. **Strategic Indexing**: Multi-column indexes for common query patterns
2. **JSON Field Optimization**: Proper JSON indexing for keypoint searches
3. **Partitioning Strategy**: Time-based partitioning for audit logs
4. **Caching Layer**: Redis for frequently accessed configuration data

## Migration Strategy
1. **Phase 1**: Core entities (User, KeypointSchema, ImageBatch, Image)
2. **Phase 2**: Workflow entities (BatchAssignment, Annotation, Verification)
3. **Phase 3**: Analytics entities (AuditLog, PerformanceMetrics, MLModelConfig)
4. **Phase 4**: Optimization and indexing improvements

This schema provides a robust foundation for the medical-grade keypoint annotation system while maintaining flexibility for future enhancements and scalability requirements.