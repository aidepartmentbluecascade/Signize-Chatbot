#!/usr/bin/env python3
"""
Test script for Dropbox integration
"""

import dropbox
import os
from datetime import datetime

# Dropbox configuration
DROPBOX_ACCESS_TOKEN = "sl.u.AF4x65ThacbAYtb7n8P1sdFtphrXInO1hi7XXi4V713kPBOyu14h72A39pPQtbrBGhG_dASY_yHxhr9B5HOlxnAFdHUSZTTyaZ0qNL0vGDyGviNDNl-qViVSvrx1tDnrCBqo8AD2e9TCPOOdqCD6G8DI_CATAHXGAMF58HDgYeqzXTAma6A1GjruHg9vxuuuvBbsfzcJRLwssQaHBWA3Mq0sKnHdHg0xYgRaRRb5S8BFEoNWJrjYg2OvQkTjltyzW6u_TTPm4RlPDoto9s-Cnb_fLrekJVl6sNMVKlpxduXgkNYzoDqT95Cc-Bp4dMDTOQEoT8CPKOmvvKMro0gZmRGDMBfU8TtiF9ymD0DweusHl1tspx0BdQgE2q50UwwhCZfZ6rQ0q0cVMIH5vZ68POW1UCtqlEL2zo6ZHkwlg8XlceFf56RJqR47g2eAZoZoCHZjwjBBBTci9r5qVNLR0DmhqeFsDTE7OXM6Ab678oOQhrPTCCUC4uGQdA03CXGjMRxZTDGRcGbdo5FLLRhRrXcs0E1nhTGFLDXBRKrLoxz_R-kdpXXslspvh4d5y6fbgx7Fg1j9nZGW3Y38tP6tqS0BcNYlwdGCnT2Ho9dYCDsvocbQ9DoypFJqNqj1dzEbyRjHScYWDnpCh7o2x1v9M5cdCv51esVjTby0iRGxYPbTFZrxF9I18bkXsRdGIG9vxzZ9aD84V5-afnUYH_I20Cy7QWakqcLEswlQhCwdBTPFtW0M3fiH_BuqXmKYTaBHnpCwolxZ470pbqob8Uw2Cp1CoO2HG7Q0NE7CMfGczXhghZUDqG-V8hNmouxldnj6X9yotpZJw3XR2VcHkyg_7K1yMhN2LB5Dw8VgAO4XUkItcT-lIZst18Xbr_YjGtp8qz26vqFUMek5dmjSL5v8sNG38INn0aO1woqkdyrBKd4ZDHKZOwBRjVYx1uJTxh8EQAPUvXgnDKi0e8OE5oUTuLItk06I08S5fdXHV1Jexdy-vjzKxhh42a0a1rPY8KzRbHYim8MBfW0xsWcgSL-57dn0R16zGMJr703FFkWisoUMJUSq7dNOSQ20lS8B81Eb9A2ymXFbCEHKucP2LeHlQHCQhmsy9a5vaz9idJV3SJMGqo3P2JqzqvBFQzJ-RGSR7qJhS1sF3NOKS3vbwMu7K59YMqAj6d5R0vIlRGwtmkJ3a9pItU8G6HSJdHdtiyKHjRRc_MRwz0OPzQblMPS1TeBPmsZ2FoH3hp_Um-8bPVW0rMTpaNT-KOKxhBCC7_tX4jzMLT2mbkKHCFG6Xlm0UILZG4kUeWRO1Krtp9GW5feTLRC7Wjp_b1R_Z3DHATaEUDsmoJgB7cDGyJ4hducOqsSB2rfzJd4QmBrIATSOELFUPVColxpWVq5cxc9TTRYz7Z7-RooKJKS-zqGZMIQsL407"

def test_dropbox_connection():
    """Test Dropbox connection and basic operations"""
    try:
        # Initialize Dropbox client
        dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
        
        # Test connection by getting account info
        account = dbx.users_get_current_account()
        print(f"✅ Dropbox connection successful!")
        print(f"   Account: {account.name.display_name}")
        print(f"   Email: {account.email}")
        
        # Test creating a test file
        test_content = f"Test file created at {datetime.now().isoformat()}"
        test_path = "/test_connection.txt"
        
        try:
            dbx.files_upload(test_content.encode(), test_path, mode=dropbox.files.WriteMode.overwrite)
            print(f"✅ Test file uploaded successfully: {test_path}")
            
            # Test creating a shared link
            try:
                link_metadata = dbx.sharing_create_shared_link_with_settings(test_path)
                url = link_metadata.url.replace("?dl=0", "?dl=1")
                print(f"✅ Shared link created: {url}")
            except dropbox.exceptions.ApiError as e:
                if isinstance(e.error, dropbox.sharing.CreateSharedLinkWithSettingsError):
                    links = dbx.sharing_list_shared_links(test_path).links
                    if links:
                        url = links[0].url.replace("?dl=0", "?dl=1")
                        print(f"✅ Existing shared link found: {url}")
                    else:
                        print(f"❌ Failed to create shared link: {e}")
                else:
                    print(f"❌ Failed to create shared link: {e}")
            
            # Clean up test file
            try:
                dbx.files_delete_v2(test_path)
                print(f"✅ Test file cleaned up")
            except Exception as e:
                print(f"⚠️  Could not clean up test file: {e}")
                
        except Exception as e:
            print(f"❌ Failed to upload test file: {e}")
            
        return True
        
    except Exception as e:
        print(f"❌ Dropbox connection failed: {e}")
        return False

def test_upload_function():
    """Test the upload_to_dropbox function from app.py"""
    try:
        # Import the function from app.py
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        from app import upload_to_dropbox
        
        # Create a test file
        test_file_path = "test_logo.txt"
        test_content = f"Test logo file created at {datetime.now().isoformat()}"
        
        with open(test_file_path, 'w') as f:
            f.write(test_content)
        
        # Test upload
        dropbox_path = "/test_logos/test_logo.txt"
        url = upload_to_dropbox(test_file_path, dropbox_path)
        
        if url:
            print(f"✅ upload_to_dropbox function works!")
            print(f"   Uploaded to: {dropbox_path}")
            print(f"   Shared URL: {url}")
        else:
            print(f"❌ upload_to_dropbox function failed")
        
        # Clean up local test file
        os.remove(test_file_path)
        
        return url is not None
        
    except Exception as e:
        print(f"❌ Test upload function failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Dropbox Integration...")
    print("=" * 50)
    
    # Test 1: Basic connection
    print("\n1. Testing Dropbox connection...")
    connection_ok = test_dropbox_connection()
    
    # Test 2: Upload function
    print("\n2. Testing upload function...")
    upload_ok = test_upload_function()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   Connection: {'✅ PASS' if connection_ok else '❌ FAIL'}")
    print(f"   Upload Function: {'✅ PASS' if upload_ok else '❌ FAIL'}")
    
    if connection_ok and upload_ok:
        print("\n🎉 All tests passed! Dropbox integration is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the configuration.")
