"""AI/ML project templates for Messirve."""

from typing import Any

AI_ML_TEMPLATES: dict[str, dict[str, Any]] = {
    "eda-scikit": {
        "name": "EDA with Scikit-Learn",
        "description": "Exploratory Data Analysis pipeline using scikit-learn",
        "tasks": [
            {
                "id": "EDA-001",
                "title": "Setup Data Analysis Environment",
                "description": """Set up a Python environment for data analysis with the following:
- Create a pyproject.toml with Poetry
- Install pandas, numpy, scikit-learn, matplotlib, seaborn, jupyter
- Create a notebooks/ directory for Jupyter notebooks
- Create a src/ directory for reusable code
- Add a basic README explaining the project structure""",
                "context": "New data science project starting from scratch",
                "acceptance_criteria": [
                    "pyproject.toml exists with all dependencies",
                    "Project structure created (notebooks/, src/, data/)",
                    "README.md with project overview",
                ],
                "flavor": "production-ready",
            },
            {
                "id": "EDA-002",
                "title": "Create Data Loading Module",
                "description": """Create a data loading module in src/data_loader.py that:
- Loads CSV, Excel, and JSON files
- Handles missing data detection
- Provides basic data info (shape, dtypes, missing values)
- Returns a pandas DataFrame with automatic type inference""",
                "context": "Project structure already set up with pandas installed",
                "acceptance_criteria": [
                    "DataLoader class with load() method",
                    "Support for CSV, Excel, JSON formats",
                    "get_info() method returns data summary",
                    "Unit tests for data loading",
                ],
                "depends_on": ["EDA-001"],
                "flavor": "production-ready",
            },
            {
                "id": "EDA-003",
                "title": "Build EDA Notebook",
                "description": """Create a Jupyter notebook notebooks/01_eda.ipynb that performs:
1. Data loading and initial exploration
2. Summary statistics (describe, info, value_counts)
3. Missing data visualization
4. Distribution plots for numerical features
5. Correlation heatmap
6. Box plots for outlier detection
7. Categorical feature analysis
8. Key insights summary""",
                "context": "Data loader module available in src/data_loader.py",
                "acceptance_criteria": [
                    "Notebook runs end-to-end without errors",
                    "All visualizations display correctly",
                    "Markdown cells explain each analysis step",
                    "Key findings documented at the end",
                ],
                "depends_on": ["EDA-002"],
                "flavor": "exploration",
            },
            {
                "id": "EDA-004",
                "title": "Create Feature Engineering Module",
                "description": """Create src/feature_engineering.py with functions for:
- Handling missing values (imputation strategies)
- Encoding categorical variables (one-hot, label, target encoding)
- Feature scaling (StandardScaler, MinMaxScaler, RobustScaler)
- Creating polynomial features
- Feature selection (variance threshold, correlation-based)
Use scikit-learn transformers and create a pipeline builder.""",
                "context": "EDA completed, need preprocessing pipeline",
                "acceptance_criteria": [
                    "FeatureEngineer class with transform methods",
                    "Pipeline builder for chaining transformations",
                    "Unit tests for each transformation",
                    "Docstrings with usage examples",
                ],
                "depends_on": ["EDA-003"],
                "flavor": "production-ready",
            },
        ],
    },
    "rag-langchain": {
        "name": "RAG with LangChain",
        "description": "Retrieval-Augmented Generation system using LangChain",
        "tasks": [
            {
                "id": "RAG-001",
                "title": "Setup LangChain Project",
                "description": """Initialize a RAG project with:
- Poetry project with langchain, langchain-openai, chromadb, tiktoken
- Environment variable handling with python-dotenv
- Project structure: src/rag/, tests/, docs/
- Configuration management for different LLM providers
- .env.example with required API keys""",
                "context": "New project for building a RAG system",
                "acceptance_criteria": [
                    "pyproject.toml with all dependencies",
                    "Config loader for API keys",
                    ".env.example documented",
                    "Basic project structure in place",
                ],
                "flavor": "production-ready",
            },
            {
                "id": "RAG-002",
                "title": "Implement Document Loader",
                "description": """Create src/rag/document_loader.py that:
- Loads documents from PDF, TXT, MD, and DOCX files
- Uses LangChain document loaders
- Implements chunking strategies (recursive, by tokens, by sentences)
- Adds metadata (source, page number, chunk index)
- Handles large documents efficiently""",
                "context": "LangChain project initialized",
                "acceptance_criteria": [
                    "DocumentLoader class supporting multiple formats",
                    "Configurable chunking (size, overlap)",
                    "Metadata preserved in chunks",
                    "Unit tests with sample documents",
                ],
                "depends_on": ["RAG-001"],
                "flavor": "production-ready",
            },
            {
                "id": "RAG-003",
                "title": "Build Vector Store",
                "description": """Create src/rag/vector_store.py that:
- Uses ChromaDB for vector storage
- Implements embedding generation (OpenAI or local)
- Supports adding, updating, and deleting documents
- Provides similarity search with score thresholds
- Persists data to disk for reuse""",
                "context": "Document loader ready",
                "acceptance_criteria": [
                    "VectorStore class with CRUD operations",
                    "Configurable embedding model",
                    "Persistence and loading from disk",
                    "Search with configurable top_k and threshold",
                ],
                "depends_on": ["RAG-002"],
                "flavor": "production-ready",
            },
            {
                "id": "RAG-004",
                "title": "Create RAG Chain",
                "description": """Create src/rag/chain.py that:
- Builds a retrieval-augmented generation chain
- Uses LangChain's LCEL (LangChain Expression Language)
- Implements custom prompts for Q&A
- Handles context window limits
- Returns sources with answers""",
                "context": "Vector store implemented",
                "acceptance_criteria": [
                    "RAGChain class with query() method",
                    "Customizable system prompt",
                    "Source documents returned with answers",
                    "Token counting and context management",
                ],
                "depends_on": ["RAG-003"],
                "flavor": "production-ready",
            },
            {
                "id": "RAG-005",
                "title": "Build CLI Interface",
                "description": """Create src/rag/cli.py with commands:
- `ingest`: Load and index documents from a directory
- `query`: Ask questions and get answers
- `clear`: Clear the vector store
- `stats`: Show indexing statistics
Use Typer for CLI and Rich for pretty output.""",
                "context": "RAG chain ready for use",
                "acceptance_criteria": [
                    "All CLI commands work correctly",
                    "Progress bars for document ingestion",
                    "Pretty-printed answers with sources",
                    "Error handling for missing API keys",
                ],
                "depends_on": ["RAG-004"],
                "flavor": "production-ready",
            },
        ],
    },
    "chatbot-openai": {
        "name": "AI Chatbot with OpenAI",
        "description": "Conversational chatbot with memory using OpenAI API",
        "tasks": [
            {
                "id": "CHAT-001",
                "title": "Setup Chatbot Project",
                "description": """Create a chatbot project with:
- Poetry project with openai, tiktoken, rich
- Async support with httpx
- Configuration for different models (gpt-4, gpt-3.5-turbo)
- Rate limiting and retry logic
- Cost tracking per conversation""",
                "context": "Building a conversational AI assistant",
                "acceptance_criteria": [
                    "Project structure created",
                    "OpenAI client wrapper with retries",
                    "Model configuration system",
                    "Basic cost calculator",
                ],
                "flavor": "production-ready",
            },
            {
                "id": "CHAT-002",
                "title": "Implement Conversation Memory",
                "description": """Create src/chatbot/memory.py that:
- Stores conversation history
- Implements sliding window memory (last N messages)
- Summarizes old messages to save tokens
- Persists conversations to disk (JSON)
- Supports multiple conversation sessions""",
                "context": "OpenAI client ready",
                "acceptance_criteria": [
                    "ConversationMemory class",
                    "Configurable memory window",
                    "Auto-summarization for long conversations",
                    "Session management (save/load)",
                ],
                "depends_on": ["CHAT-001"],
                "flavor": "production-ready",
            },
            {
                "id": "CHAT-003",
                "title": "Build Chat Interface",
                "description": """Create src/chatbot/chat.py with:
- Interactive CLI chat using Rich
- Streaming responses for better UX
- System prompt customization
- Commands: /clear, /save, /load, /system, /exit
- Token usage display after each response""",
                "context": "Memory system implemented",
                "acceptance_criteria": [
                    "Interactive chat loop works",
                    "Streaming output displays correctly",
                    "All slash commands functional",
                    "Token/cost tracking displayed",
                ],
                "depends_on": ["CHAT-002"],
                "flavor": "production-ready",
            },
            {
                "id": "CHAT-004",
                "title": "Add Function Calling",
                "description": """Extend the chatbot with function calling:
- Define tools (get_weather, search_web, calculate)
- Implement tool execution framework
- Handle tool responses in conversation
- Add safety checks for tool execution""",
                "context": "Basic chatbot working",
                "acceptance_criteria": [
                    "At least 3 tools defined and working",
                    "Tool results integrated in responses",
                    "Error handling for failed tools",
                    "Tools documented in help command",
                ],
                "depends_on": ["CHAT-003"],
                "flavor": "production-ready",
            },
        ],
    },
    "aws-ml-infra": {
        "name": "AWS ML Infrastructure",
        "description": "Infrastructure as Code for ML workloads on AWS",
        "tasks": [
            {
                "id": "AWS-001",
                "title": "Setup Terraform Project",
                "description": """Create Terraform project for ML infrastructure:
- Initialize Terraform with AWS provider
- Set up remote state in S3 with DynamoDB locking
- Create modules structure: vpc/, sagemaker/, s3/, iam/
- Configure workspaces for dev/staging/prod
- Add .gitignore for Terraform files""",
                "context": "New AWS ML infrastructure project",
                "acceptance_criteria": [
                    "Terraform initialized with AWS provider",
                    "Remote state configured",
                    "Module structure created",
                    "Workspace configuration documented",
                ],
                "flavor": "production-ready",
            },
            {
                "id": "AWS-002",
                "title": "Create VPC Module",
                "description": """Create modules/vpc/ with:
- VPC with public and private subnets
- NAT Gateway for private subnet internet access
- Security groups for ML workloads
- VPC endpoints for S3 and ECR
- Outputs for subnet IDs and security group IDs""",
                "context": "Terraform project initialized",
                "acceptance_criteria": [
                    "VPC with 2 AZs minimum",
                    "Public and private subnets",
                    "NAT Gateway configured",
                    "VPC endpoints for AWS services",
                ],
                "depends_on": ["AWS-001"],
                "flavor": "production-ready",
            },
            {
                "id": "AWS-003",
                "title": "Create S3 Data Lake Module",
                "description": """Create modules/s3/ for ML data storage:
- Raw data bucket with versioning
- Processed data bucket
- Model artifacts bucket
- Lifecycle policies for cost optimization
- Bucket policies for SageMaker access
- Server-side encryption (SSE-S3)""",
                "context": "VPC module ready",
                "acceptance_criteria": [
                    "Three S3 buckets created",
                    "Versioning enabled on raw bucket",
                    "Lifecycle policies configured",
                    "Encryption enabled",
                ],
                "depends_on": ["AWS-002"],
                "flavor": "production-ready",
            },
            {
                "id": "AWS-004",
                "title": "Create SageMaker Module",
                "description": """Create modules/sagemaker/ with:
- SageMaker Domain for Studio
- Execution role with necessary permissions
- Notebook instance configuration
- Training job configuration template
- Model endpoint configuration
- Auto-scaling for endpoints""",
                "context": "VPC and S3 modules ready",
                "acceptance_criteria": [
                    "SageMaker Domain created",
                    "IAM roles properly scoped",
                    "Notebook instance launchable",
                    "Endpoint auto-scaling configured",
                ],
                "depends_on": ["AWS-003"],
                "flavor": "production-ready",
            },
            {
                "id": "AWS-005",
                "title": "Create CI/CD Pipeline",
                "description": """Add GitHub Actions workflows for:
- Terraform fmt and validate on PR
- Terraform plan on PR (post as comment)
- Terraform apply on merge to main
- Cost estimation using Infracost
- Security scanning with tfsec""",
                "context": "All Terraform modules ready",
                "acceptance_criteria": [
                    "PR workflow runs fmt, validate, plan",
                    "Plan output posted to PR",
                    "Main branch triggers apply",
                    "Cost estimates in PR comments",
                ],
                "depends_on": ["AWS-004"],
                "flavor": "production-ready",
            },
        ],
    },
    "ml-pipeline": {
        "name": "ML Training Pipeline",
        "description": "End-to-end ML pipeline with MLflow tracking",
        "tasks": [
            {
                "id": "MLP-001",
                "title": "Setup ML Project Structure",
                "description": """Create an ML project with:
- Poetry with scikit-learn, pandas, mlflow, hydra-core
- Project structure: src/data/, src/features/, src/models/, src/evaluation/
- Configuration using Hydra (conf/ directory)
- MLflow tracking setup (local or remote)
- DVC for data versioning (optional)""",
                "context": "New ML project with experiment tracking needs",
                "acceptance_criteria": [
                    "Project structure created",
                    "Hydra config files set up",
                    "MLflow tracking configured",
                    "README with setup instructions",
                ],
                "flavor": "production-ready",
            },
            {
                "id": "MLP-002",
                "title": "Implement Data Pipeline",
                "description": """Create src/data/pipeline.py with:
- Data loading from multiple sources
- Train/validation/test splitting with stratification
- Data validation checks
- Caching for processed data
- Integration with Hydra config""",
                "context": "Project structure ready",
                "acceptance_criteria": [
                    "DataPipeline class with run() method",
                    "Configurable split ratios",
                    "Data validation reports",
                    "Caching reduces reprocessing",
                ],
                "depends_on": ["MLP-001"],
                "flavor": "production-ready",
            },
            {
                "id": "MLP-003",
                "title": "Build Model Training Module",
                "description": """Create src/models/trainer.py with:
- Support for multiple model types (sklearn, xgboost, lightgbm)
- Hyperparameter configuration via Hydra
- Cross-validation support
- Early stopping where applicable
- MLflow experiment tracking
- Model serialization""",
                "context": "Data pipeline ready",
                "acceptance_criteria": [
                    "Trainer class supporting multiple models",
                    "Metrics logged to MLflow",
                    "Models saved with artifacts",
                    "Reproducible training with seeds",
                ],
                "depends_on": ["MLP-002"],
                "flavor": "production-ready",
            },
            {
                "id": "MLP-004",
                "title": "Create Evaluation Module",
                "description": """Create src/evaluation/evaluator.py with:
- Classification metrics (accuracy, precision, recall, F1, AUC-ROC)
- Regression metrics (MSE, RMSE, MAE, R²)
- Confusion matrix visualization
- Feature importance plots
- SHAP values for model explanability
- Comparison across experiments""",
                "context": "Training pipeline working",
                "acceptance_criteria": [
                    "Evaluator class with comprehensive metrics",
                    "Visualizations saved as artifacts",
                    "SHAP integration working",
                    "Experiment comparison report",
                ],
                "depends_on": ["MLP-003"],
                "flavor": "production-ready",
            },
            {
                "id": "MLP-005",
                "title": "Build CLI and Entry Points",
                "description": """Create CLI for the ML pipeline:
- `train`: Run training with Hydra config overrides
- `evaluate`: Evaluate a saved model
- `predict`: Make predictions with a model
- `compare`: Compare multiple experiments
- `serve`: Serve model via REST API (optional)""",
                "context": "All pipeline components ready",
                "acceptance_criteria": [
                    "All CLI commands functional",
                    "Hydra config overrides work",
                    "Useful logging and progress bars",
                    "Documentation for each command",
                ],
                "depends_on": ["MLP-004"],
                "flavor": "production-ready",
            },
        ],
    },
}
