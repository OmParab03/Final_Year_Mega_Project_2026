# Toxi-Scan: AI-Based Personalized Skincare Analyzer

> An intelligent, two-phase skincare assistant that combines deep learning, computer vision, OCR, NLP, and cosmetic ingredient analysis to tell users whether a product is actually safe for **their specific skin** — not just what the star ratings say.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Problem Statement](#problem-statement)
3. [Key Innovation](#key-innovation)
4. [Objectives](#objectives)
5. [Scope](#scope)
6. [System Architecture](#system-architecture)
7. [How It Works (Two-Phase Flow)](#how-it-works-two-phase-flow)
8. [Tech Stack](#tech-stack)
9. [Hardware Requirements](#hardware-requirements)
10. [Product Functions / Modules](#product-functions--modules)
11. [Functional Requirements](#functional-requirements)
12. [Non-Functional / Performance Requirements](#non-functional--performance-requirements)
13. [Design Constraints](#design-constraints)
14. [Database Design (MongoDB)](#database-design-mongodb)
15. [Software Design Artifacts](#software-design-artifacts)
16. [Core Algorithms](#core-algorithms)
17. [Software System Attributes](#software-system-attributes)
18. [Out of Scope](#out-of-scope)
19. [Team & Guidance](#team--guidance)
20. [References](#references)

---

## Project Overview

**Toxi-Scan** is a final-year B.Tech project from the Department of Computer Science & Engineering (AI & ML), D.K.T.E. Society's Textile and Engineering Institute, Ichalkaranji (Affiliated to Shivaji University, Kolhapur), for academic year 2025-26.

The system is formally titled **"AI-Based Personalized Skincare Analyzer"** and is built to solve a very concrete consumer problem: people buy skincare/cosmetic products based on reviews, ratings, and marketing — not based on whether the actual **ingredient composition** is compatible with their **actual skin condition**. Toxi-Scan fixes this by combining:

- **Facial image analysis** (deep learning) to determine real skin type and detect visible conditions (acne, pigmentation, redness, etc.)
- **OCR + NLP** to read and parse the ingredient list off a photographed product label
- **Ingredient knowledge base matching** to score each ingredient's safety/suitability
- **Personalized risk analysis** that cross-references ingredients against the user's skin profile and allergies
- **Explainable AI (XAI)** so the verdict ("Safe" / "Harmful") always comes with a human-readable *reason*

---

## Problem Statement

> Existing skincare recommendation systems fail to provide accurate and personalized product analysis because they do not effectively combine real skin condition analysis with ingredient-level evaluation.

### Key problems identified in existing systems
| # | Problem | Why it matters |
|---|---------|-----------------|
| 1 | **No ingredient-based analysis** | Ingredients determine real product efficacy, but most systems ignore them entirely. |
| 2 | **No accurate skin condition analysis** | Systems rely on self-reported/generic skin types, which users often get wrong. |
| 3 | **Limited personalization** | Collaborative/content-based filtering focuses on user behavior, not biological skin characteristics. |
| 4 | **Poor integration of AI techniques** | Some systems do skin analysis *or* ingredient analysis, but rarely combine both reliably. |
| 5 | **Ingredient lists are hard to interpret** | Consumers want to understand ingredients post health-awareness trends, but lists are complex and combination effects aren't explained. |

---

## Key Innovation

Unlike traditional recommendation systems, Toxi-Scan:

- Does **not** rely only on user reviews
- Uses **actual ingredient composition + AI skin analysis + an Analysis Dashboard**
- Provides **scientifically driven reasons** for every verdict (via Explainable AI)

---

## Objectives

1. **Dashboard/UI & Data Collection** — user-friendly interface to collect user images and skin details.
2. **Skin Assessment (Deep Learning)** — classify skin type: oily, dry, combination.
3. **Skin Condition Detection** — detect the face, extract the skin region, identify acne, pigmentation, redness, etc.
4. **Explainable Output** — every result comes with a clear, understandable justification.
5. **Automated Data Extraction** — OCR-based ingredient extraction from product label photos, matched against a knowledge base.
6. **Personalized Risk Assessment** — compare product ingredients against the user's skin type/allergies to flag harmful or unsuitable components.

### High-level Goals
- Improve accuracy vs. review-only systems by using ingredient-level insight + AI skin analysis.
- Enable automated, objective skin condition assessment.
- Reduce trial-and-error in skincare purchases.

### Benefits
- More accurate ingredient analysis
- Better consumer understanding of ingredients
- Saves time and money
- Reduces trial-and-error
- Prevents use of risky products

---

## Scope

### The system WILL:
- Analyze a user's facial image to detect: acne, wrinkles, pigmentation, redness, pores, dark circles
- Process cosmetic product ingredient compositions to predict effectiveness for different skin conditions
- Match user skin conditions with suitable products (recommendation engine)
- Provide personalized recommendations across categories: cleansers, toners, serums, moisturizers

### The system will NOT:
- Provide medical diagnosis or replace professional dermatological advice
- Guarantee clinical results from recommended products
- Handle surgical or advanced dermatological treatment recommendations

---

## System Architecture

Toxi-Scan follows a **layered microservice-style architecture**:

```
┌───────────────────────────────────────────────────────────────────┐
│ CLIENT LAYER                                                        │
│  Web App (Angular)   |   Mobile App   |   Browser Camera (capture)  │
└───────────────────────────────┬───────────────────────────────────┘
                                 │
┌───────────────────────────────▼───────────────────────────────────┐
│ API GATEWAY LAYER                                                    │
│  REST API Gateway   |   Auth Middleware (JWT)   |   Rate Limiter     │
└───────────────────────────────┬───────────────────────────────────┘
                                 │
┌───────────────────────────────▼───────────────────────────────────┐
│ BACKEND SERVICES LAYER                                               │
│  User Service (auth, profile, history)                               │
│  Skin Analysis Service (DL model inference)                          │
│  OCR Service (Tesseract / TrOCR)                                     │
│  NLP Service (Transformers)                                          │
│  Risk Analysis Service (ingredient scoring)                          │
│  Notification Service (email)                                        │
│  LLM Explanation Service (API calls for explainable output)          │
│  Image Preprocessing (OpenCV — enhance, denoise)                     │
│                         ↕ Message Queue                              │
└───────────────────────────────┬───────────────────────────────────┘
                                 │
┌───────────────────────────────▼───────────────────────────────────┐
│ DATA LAYER (MongoDB)                                                 │
│  User Collection (profiles + history)                                │
│  Ingredient Collection (safety knowledge base)                       │
│  Image Store (uploads + scans — metadata/refs; binaries in           │
│               object/cloud storage)                                  │
│  Cache (session + results)                                           │
└───────────────────────────────────────────────────────────────────┘
```

> **Note:** The original SRS diagrams reference MySQL for the data layer; this implementation uses **MongoDB** instead, since the domain data (ingredient knowledge graphs, nested skin-analysis results, flexible product/ingredient documents) fits a document-oriented model more naturally than a fixed relational schema. See [Database Design](#database-design-mongodb) below for how the original ER design was translated into MongoDB collections.
>
> As of the MongoDB migration, `users`, `user_settings`, and `skin_analyses` (the skin-analysis flow described below, backed by two Hugging Face model endpoints) are implemented against a live MongoDB Atlas cluster. The `products` / `ingredients` / `scan_history` collections for the OCR + ingredient-risk pipeline (Phase 2) are still the target design, not yet built.

---

## How It Works (Two-Phase Flow)

### Phase 1 — User Onboarding / Profiling
```
Start Registration → Enter Personal Details (Name, Age, Allergies)
      → Upload/Capture Skin Image → Skin Analysis Module (AI)
      → Store User Profile
```

### Phase 2 — Product Analysis
```
Start Product Analysis → Image Processing → Text Detection
      → OCR Engine → Ingredient Extraction (NLP)
      → Ingredient Database Lookup → Risk Analysis Engine
      → Personalization (skin type + allergies)
      → Explainable AI Module → Final Output (Safe / Harmful + Reason)
      → Detailed Ingredient Report → Analytics Dashboard
```

**In short:** the user builds a skin profile once (Phase 1), then can scan as many products as they like (Phase 2), each time getting a personalized Safe/Harmful verdict with a plain-English explanation.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Angular (web), mobile-compatible UI, browser camera capture |
| **Backend** | Python (Flask) |
| **AI / ML — Skin Analysis** | EfficientNet-B0 (skin type classification), YOLOv8n (skin condition/object detection) |
| **AI / ML — Frameworks** | TensorFlow / PyTorch |
| **Image Processing** | OpenCV (denoise, enhance, contrast/CLAHE, sharpen) |
| **OCR** | Tesseract / TrOCR |
| **NLP** | spaCy / Transformers (ingredient NER + normalization) |
| **Explainability** | LLM APIs (GPT / Claude) for human-readable explanations |
| **Database** | **MongoDB** (document store for users, ingredients, scan history, analytics) |
| **Auth** | JWT-based auth middleware |
| **Cloud / Infra** | AWS (cloud services), REST APIs, message queue for async service communication |

---

## Hardware Requirements

**Client side**
- Smartphone / Laptop / Desktop
- Camera (for capturing skin and product images)
- Minimum 4 GB RAM

**Server side**
- Cloud server / local server
- Minimum 8 GB RAM
- GPU (optional, for faster AI/DL inference)

---

## Product Functions / Modules

1. **User Registration & Login** — account creation and access
2. **User Profile Creation (Phase 1)** — collects Name, Age, Allergies; allows skin image upload/capture
3. **Skin Analysis** — AI determines skin type (oily/dry/sensitive/combination) and possible conditions
4. **Product Image Upload** — user uploads a product label photo
5. **Image Processing** — enhances image for better text detection (OpenCV pipeline)
6. **Text Detection & OCR** — detects text regions, extracts ingredient text
7. **Ingredient Extraction** — NLP identifies ingredient names from raw OCR text
8. **Ingredient Analysis** — matches extracted ingredients against the knowledge base, determines safety level
9. **Personalized Risk Analysis** — cross-references skin type + allergies to generate a personalized result
10. **Explainable AI Output** — returns result (Safe/Harmful) + the *reason* behind it
11. **Analytics Dashboard** — tracks scanned products, risk history, user insights over time

---

## Functional Requirements

**User Management**
- The system shall allow users to register with personal details.
- The system shall authenticate users via login.

**Profile Creation**
- The system shall store user allergies and preferences.
- The system shall allow image upload for skin analysis.

**Skin Analysis**
- The system shall process skin images using AI models.
- The system shall classify skin type and detect conditions.

**Product Analysis**
- The system shall accept product images.
- The system shall preprocess images for clarity.

**Text Extraction**
- The system shall detect text regions.
- The system shall extract text using OCR.

**Ingredient Processing**
- The system shall identify ingredient names using NLP.
- The system shall normalize ingredient names (standardize to canonical/INCI names).

**Risk Analysis**
- The system shall compare ingredients against the ingredient database.
- The system shall detect harmful ingredients.
- The system shall personalize results using the user profile.

**Output Generation**
- The system shall display results (Safe / Harmful).
- The system shall provide an AI-generated explanation.

**Analytics**
- The system shall store user history.
- The system shall provide dashboard insights.

---

## Non-Functional / Performance Requirements

**Static / Capacity**
- Support up to **5,000 users**
- Support **500 concurrent users**
- Store large image and text datasets

**Dynamic / Latency Targets**
| Operation | Target |
|---|---|
| Image processing time | ≤ 10 seconds |
| OCR processing time | ≤ 5 seconds |
| Response generation | ≤ 3 seconds |
| Peak load | Must be handled efficiently |

---

## Design Constraints

- Python-based backend frameworks
- Must integrate AI/ML models directly into the request pipeline
- Accuracy is dependent on OCR quality (lighting, image resolution, label design)
- Limited by available hardware (CPU/GPU)
- Must follow applicable privacy and data protection policies

---

## Database Design (MongoDB)

The original SRS specifies a relational ER model (Users, SkinAnalysisRecord, Product, Ingredient, ProductIngredient, ScanHistory, IngredientSuitability). This project implements that same logical model using **MongoDB collections**, favoring embedding for one-to-few relationships and referencing for many-to-many / high-growth relationships.

### Collections

**`users`**
```json
{
  "_id": ObjectId,
  "name": "string",
  "age": "number",
  "email": "string (unique)",
  "passwordHash": "string",
  "skinType": "oily | dry | combination | sensitive",
  "allergies": ["string"],
  "createdAt": "ISODate",
  "updatedAt": "ISODate"
}
```

**`skin_analysis_records`** (referenced from `users`, one-to-many)
```json
{
  "_id": ObjectId,
  "userId": ObjectId,        // ref -> users._id
  "analysisDate": "ISODate",
  "skinTypeResult": "string",
  "detectedConditions": [
    { "condition": "acne", "confidence": 0.87 },
    { "condition": "pigmentation", "confidence": 0.62 }
  ],
  "sourceImageRef": "string"  // pointer to object/cloud storage, not raw binary
}
```

**`products`**
```json
{
  "_id": ObjectId,
  "productName": "string",
  "brand": "string",
  "category": "cleanser | toner | serum | moisturizer | other",
  "ingredients": [
    { "ingredientId": ObjectId, "concentration": "number | null" }
  ]
}
```

**`ingredients`** (the knowledge base — high read frequency)
```json
{
  "_id": ObjectId,
  "ingredientName": "string",
  "normalizedName": "string (unique, INCI-style)",
  "properties": ["string"],
  "benefits": ["string"],
  "risks": ["string"],
  "suitability": [
    { "skinType": "oily", "condition": "acne", "level": "Recommended | Caution | Avoid" }
  ]
}
```

**`scan_history`**
```json
{
  "_id": ObjectId,
  "userId": ObjectId,        // ref -> users._id
  "productId": ObjectId,     // ref -> products._id
  "scanDate": "ISODate",
  "safetyResult": "Safe | Harmful",
  "explanation": "string",
  "harmfulIngredients": ["string"],
  "unsuitableIngredients": ["string"]
}
```

### Why MongoDB (vs. the SRS's relational default)
- **Flexible ingredient documents** — ingredients have variable-length, nested arrays (properties, benefits, risks, per-skin-type suitability) that map naturally to sub-documents instead of extra join tables.
- **Fast reads for high-frequency data** — user auth data, skin analysis results, and the ingredient knowledge base are all marked "High" frequency in the SRS; document lookups avoid multi-table joins on the hot path.
- **Schema evolution** — as new AI models add new detected-condition types or new ingredient metadata fields, MongoDB tolerates schema growth without migrations.
- **Natural fit for the Explainable-AI payloads** — variable-shape explanation objects (per-ingredient reasoning) embed cleanly.

### Data Integrity Rules (carried over from the SRS)
- **Entity integrity:** every document has a unique, non-null `_id`.
- **Referential integrity:** application-layer checks ensure `userId` / `productId` / `ingredientId` references point to existing documents (MongoDB has no native FK enforcement, so this is enforced in the service layer, with cascading/soft-delete logic on account deletion).
- **Domain integrity:**
  - `email` unique + valid format
  - `passwordHash` never null
  - `ingredientName` / `normalizedName` unique
  - `safetyResult` ∈ {Safe, Harmful}
  - `suitabilityLevel` ∈ {Recommended, Caution, Avoid}
- **User-defined integrity:** minimum age requirement enforced at registration; ingredient concentration values bounded to valid numeric ranges.

### Data Retention
- User profile data retained while the account is active; anonymized/removed after a configurable grace period post-deletion.
- Skin analysis + scan history retained to support personalization/trend analysis, unless the user requests deletion.
- Uploaded images (skin + product) retained only as long as needed for processing, then auto-deleted unless the user consents to longer storage.
- Product/ingredient knowledge base retained indefinitely and updated regularly.
- System logs retained for a defined operational window before archival/deletion.
- All retention policy specifics communicated via the system's Privacy Policy.

---

## Software Design Artifacts

The full SRS includes the following UML/design artifacts (see the original SRS PDF for diagrams):

- **Class Diagram** — `User → ImageInput → TextDetection → OCREngine → IngredientParser → Ingredient → KnowledgeGraph → RiskAnalysisModel → {AllergyDetector, IrritantDetector, SkinCompatibilityChecker, InteractionAnalyzer, ExplainableAI} → OutputModule`
- **Object Diagram** — worked example: a scan of "Water, Salicylic Acid, Fragrance" resolving to *"Suitable for acne-prone skin but may cause irritation due to fragrance."*
- **Data Flow Diagrams**
  - **DFD0** — Toxi-Scan system as a single process exchanging data with User, AI/ML models, Ingredient DB, and an LLM API.
  - **DFD1** — five major processes: User Management → Skin Analysis → OCR/Ingredient Extraction → Personalized Risk Analysis → Output/Dashboard, backed by User Profile, Ingredient, and Analysis History stores.
  - **DFD2** — zoom into the OCR/ingredient-extraction sub-process: image upload → preprocessing (OpenCV) → text region detection → OCR (Tesseract/TrOCR) → NLP ingredient identification → normalization → handoff to risk analysis.
- **Sequence Diagram** — full request path from `User` uploading an image through `ImageInput → TextDetection → OCREngine → IngredientParser → KnowledgeGraph → RiskAnalysisModel → ExplainableAI → OutputModule`.
- **Collaboration Diagram** — numbered message-passing view (login → uploadImage → analyseSkin → extractText → parseIngredients → assessRisk → querySafety → generateExplanation → displayResult → storeScore → safetyReport), 20 steps total.
- **Activity Diagram** — user journey states: LoggedOut → Registered/LoggedIn → ProfileCreated → SkinAnalysis → WaitingProduct → ProductUploaded → Processing → TextDetection → OCR → Extraction → IngredientAnalysis → RiskAnalysis → (Safe | Harmful) → Result → Display.
- **Use Case Diagram** — actor `User` with use cases: Register/Login; Manage Skin Profile «include» Analyze Skin Type; Upload Skin Image «include» Extract Ingredients (OCR); Upload Product Image «include» Assess Ingredient Risk; View Safety Result «include» Generate Explanation; View Scan History.
- **State-chart Diagram** — Idle → Authenticating (retry loop) → Profile Loaded → Image Uploading → Processing (OCR + skin analysis) → Risk Analysing → Generating Explanation (LLM, with failure → Error state) → Result Ready → Logout.
- **Component Diagram** — User Interface ↔ Backend Server API, fanning out to Authentication, User Profile Management, Skin Analysis, Analytics Dashboard (→ Database), and Image Processing → OCR Engine → NLP Module → Ingredient Database, plus Risk Analysis Engine ↔ Explainable AI Module.
- **Deployment Diagram** — `AI_Server` (AI Model, OCR Engine, NLP Module) + `Web_Server` (Frontend, Backend API), reached by User Device, routed to AI Processing Server, Database Server, and Cloud Storage (for stored images).

---

## Core Algorithms

### 1. Skin Analysis
**Input:** `UserID`, `skin_image_file` → **Output:** `skin_type`, `detected_conditions`

1. Load and preprocess the skin image (resize, normalize, enhance).
2. Classify skin type using **EfficientNet-B0**; select the highest-probability class.
3. Detect skin conditions using **YOLOv8**; extract detections + confidence scores.
4. Persist skin type + detected conditions to the database.
5. Return `skin_type`, `detected_conditions`.

### 2. Product Scanning (Image Preprocessing + Condition Inference)
1. Load the image (`cv2.imread`).
2. Preprocess:
   - Resize (`cv2.resize`)
   - Denoise (`cv2.fastNlMeansDenoisingColored`)
   - Sharpen (`cv2.filter2D`)
   - Contrast enhancement (`cv2.createCLAHE`)
   - Save processed image (`cv2.imwrite`)
3. Load the trained YOLO model (`YOLO("best.pt")`).
4. Run detection; extract boxes, class labels, and confidence scores.
5. Filter detections with confidence > 0.5.
6. If nothing passes the threshold → report **"Normal Skin"**; otherwise report detected condition(s) (Acne, Redness, Pigmentation, etc.).

### 3. Ingredient Extraction
**Input:** `raw_extracted_text` → **Output:** `normalized_ingredients_list`

1. Clean OCR text (remove noise characters/formatting errors).
2. Split text into individual ingredient phrases.
3. Run NLP (spaCy/Transformer) or rule-based matching to identify ingredient tokens.
4. Normalize names (lowercase + standardize known variants).
5. Validate against the Ingredient Knowledge Base; resolve canonical names.
6. Persist the normalized list.
7. Return `normalized_ingredients_list`.

### 4. Risk Analysis
**Input:** `UserID`, `normalized_ingredients_list`
**Output:** `overall_safety_result`, `harmful_ingredients_details`, `unsuitable_ingredients_details`

1. Fetch the user's skin type + allergies.
2. For each ingredient:
   - Look up ingredient info in the knowledge base.
   - Check against user allergies.
   - Check suitability for the user's skin type.
   - Check the ingredient's general safety rating.
   - Bucket into harmful / unsuitable lists as applicable.
3. Determine overall verdict:
   - **Harmful** — if any harmful ingredient found.
   - **Potentially Harmful** — if any unsuitable (but not outright harmful) ingredient found.
   - **Safe** — otherwise.
4. Persist and return the result with details.

---

## Software System Attributes

| Attribute | Requirement |
|---|---|
| **Reliability** | High accuracy in AI predictions, minimal failure rate, robust error handling |
| **Availability** | 24/7 availability, backup and recovery support |
| **Security** | Secure login authentication, data encryption, protection from unauthorized access |
| **Maintainability** | Modular architecture, easy debugging/updates, well-documented code |
| **Portability** | Compatible with web and mobile platforms, OS-independent |

---

## Out of Scope

Toxi-Scan explicitly does **not**:
- Provide a medical diagnosis or replace a dermatologist
- Guarantee clinical outcomes from any recommended product
- Handle surgical or advanced dermatological treatment guidance

This is a **decision-support / awareness tool**, not a medical device.

---

## Team & Guidance

**Institution:** D.K.T.E. Society's Textile and Engineering Institute, Ichalkaranji
(An Empowered Autonomous Institute, Affiliated to Shivaji University, Kolhapur)
**Department:** Computer Science & Engineering (Artificial Intelligence and Machine Learning)
**Academic Year:** 2025-26

**Project Guide:** Prof. A. G. Shahane
**Head of Department:** Prof. Dr. S. K. Shirgave

**Submitted By (Group 18):**
| Roll No. | Name |
|---|---|
| 24UAM301 | Swapnil Sambhaji Bhosale |
| 22UAI065 | Anurag Balasaheb Londhe |
| 23UAM085 | Darshan Chandrakant Neje |
| 23UAM087 | Omkar Umesh Parab |
| 23UAM093 | Pradip Mallikarjun Patil |

Run commands
frontend: ng serve
backend: .\venv\Scripts\python.exe app.py

---

*This README is derived from the project's Software Requirements Specification (SRS) document and is intended to give any collaborator full context on Toxi-Scan's purpose, architecture, and design without needing to re-read the original SRS.*
