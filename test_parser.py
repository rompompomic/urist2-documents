import sys
from processor import DocumentProcessor

def test_company(name):
    print(f"Testing search for: '{name}'")
    processor = DocumentProcessor()
    inn, address = processor.parse_inn_and_address_from_rusprofile(name)
    print("--------------------------------------------------")
    print(f"Result for '{name}':")
    print(f"INN: {inn}")
    print(f"Address: {address}")
    print("--------------------------------------------------")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        name = " ".join(sys.argv[1:])
        test_company(name)
    else:
        print("Usage: python test_parser.py <company name>")
