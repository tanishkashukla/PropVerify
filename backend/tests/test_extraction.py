import glob
import os
import sys

# Ensure workspace root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.document_processing.extractor import process_document


def run_tests():
    doc_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../test_documents"))
    pdf_files = sorted(glob.glob(os.path.join(doc_dir, "*.pdf")))

    if not pdf_files:
        print(f"No PDF files found in {doc_dir}")
        return

    print("================================================================================")
    print("PROPVERIFY DOCUMENT PROCESSING AND AI EXTRACTION MODULE - TEST RUN")
    print("================================================================================\n")

    results = []

    for pdf_path in pdf_files:
        file_name = os.path.basename(pdf_path)
        print(f"Processing File: {file_name}")
        print("-" * 60)

        res = process_document(pdf_path, filename=file_name)
        results.append(res)

        print("\nPROCESSING SUMMARY:")
        print(f"  - Document Type Detected : {res.document_type_detected}")
        print(f"  - OCR Required           : {res.ocr_used}")
        print(f"  - Raw Text Length        : {res.raw_text_length} characters")
        print(f"  - Fields Extracted ({len(res.fields_extracted)}) : {', '.join(res.fields_extracted)}")
        print(f"  - Fields Missing ({len(res.fields_missing)})   : {', '.join(res.fields_missing) if res.fields_missing else 'None'}")
        print(f"  - Extraction Errors      : {len(res.errors)}")
        print(f"  - Processing Warnings    : {len(res.warnings)}")
        print("\n" + "=" * 80 + "\n")

    print("SUMMARY REPORT ACROSS ALL DOCUMENTS:")
    print("-" * 60)
    for res in results:
        print(f"File: {res.file_name:<25} | Type: {res.document_type_detected:<15} | OCR: {str(res.ocr_used):<5} | Extracted: {len(res.fields_extracted)}/10 fields")


if __name__ == "__main__":
    run_tests()
