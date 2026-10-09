import glob
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.document_processing.extractor import process_document
from backend.verification.comparator import compare_documents


def run_verification_test():
    doc_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../test_documents"))
    pdf_files = sorted(glob.glob(os.path.join(doc_dir, "*.pdf")))

    print("================================================================================")
    print("PROPVERIFY MODULE 2: VERIFICATION & COMPARISON ENGINE - FULL TEST RUN")
    print("================================================================================\n")

    results = []
    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        print(f"Loading & Extracting: {filename}...")
        res = process_document(pdf_path, filename=filename)
        results.append(res)

    print(f"\nSuccessfully extracted {len(results)} test documents.")
    print("Executing Cross-Document Verification & Comparison Engine...\n")

    verification_result = compare_documents(results)

    print("================================================================================")
    print("VERIFICATION SUMMARY:")
    print(f"  Overall status     : {verification_result.overall_status}")
    print(f"  Documents processed: {verification_result.documents_processed}")
    print(f"  Matched fields     : {len(verification_result.matches)}")
    print(f"  Mismatched fields  : {len(verification_result.mismatches)}")
    print(f"  Missing documents  : {len(verification_result.missing_documents)}")
    print(f"  Processing warnings: {len(verification_result.warnings)}")
    print("================================================================================\n")


if __name__ == "__main__":
    run_verification_test()
