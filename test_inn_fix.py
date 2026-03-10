from processor import DocumentProcessor

def test_inn_search():
    # Test INN searching
    inn = "5405967772"
    print(f"Testing INN search for {inn}...")
    res_inn, res_addr = DocumentProcessor.parse_inn_and_address_from_rusprofile(inn)
    print(f"Result: INN={res_inn}, Addr={res_addr}")
    
    if res_inn == inn:
        print("✅ SUCCESS")
    else:
        print("❌ FAILURE")

if __name__ == "__main__":
    test_inn_search()
