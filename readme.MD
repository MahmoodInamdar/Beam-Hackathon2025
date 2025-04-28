### PROMPT GENERATOR PIPELINE and DATA EXTRACTION PIPELINE



This project is an end-to-end, LLM-powered pipeline for automatically
    extracting structured data from PDF documents (specifically invoices and
    orders) that are stored as attachments in an Airtable base. It consists of
    four main stages:

        1. AirTable Attachment Extraction
           • Uses the Airtable REST API to fetch all records (with pagination)
    from a given view.
           • Downloads each attachment (PDF) to a local folder and builds a
    small CSV/JSON manifest of record metadata (file IDs, expected outputs,
    dataset‐type).
        2. PDF-to-JSON Conversion
           • Leverages pdfplumber (for structured extraction) or PyPDF for “raw”
     text.
           • Cleans OCR artifacts and normalizes whitespace, then outputs each
    page’s content into a JSON file.
        3. Prompt-Engineering & LLM Prompt Generation
           • Defines a “meta-prompt” template plus two target schemas (one for
    invoices, one for orders).
           • Automatically inspects the raw‐JSON text to detect document type
    (invoice vs. order) by keyword matching.
           • Fills in the meta-prompt and invokes OpenAI’s GPT-4-o to generate a
     bespoke, detailed extraction prompt (saved under generated_prompts/).
        4. Data Extraction, Post-Processing & Evaluation
           • Loads the refined prompts and runs another GPT-4-o call to extract
    the actual structured data (e.g. total_net, business_name, line-items,
    order_date, delivery_address, etc.).
           • Normalizes numerical fields (currencies) and dates into consistent
    formats.
           • Flattens and compares the LLM outputs against the ground-truth
    (Airtable’s “Expected Output”) using an accuracy-scoring function built on
    scikit-learn.
           • Produces a final JSON of extracted results plus an accuracy report.

    Real-World Usefulness

        * Automates repetitive, error-prone manual data-entry tasks in finance
    and supply-chain workflows (accounts-payable, order management, vendor
    onboarding, etc.).
        * Integrates seamlessly with Airtable (or any similar “no-code”
    database) to manage document ingestion and metadata.
        * Highly adaptable: you can plug in new document types by defining
    keyword mappings and JSON schemas, then auto-generate extraction prompts.
        * Delivers end-to-end visibility: from raw PDF to cleaned JSON, through
    prompt-generation, extraction, and evaluation—enabling continual improvement
     of your LLM-based OCR pipeline.
        * Serves as a reference architecture for combining traditional
    PDF-parsing libraries with modern LLMs to build robust, production-grade
    RPA/data-extraction systems.