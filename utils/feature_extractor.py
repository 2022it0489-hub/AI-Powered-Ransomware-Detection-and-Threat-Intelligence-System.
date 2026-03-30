import pefile
import hashlib
import os
import re
import pandas as pd
import math

class FeatureExtractor:
    def __init__(self):
        # Regex for Bitcoin Addresses (P2PKH, P2SH, Bech32)
        self.btc_regex = re.compile(r"([13][a-km-zA-HJ-NP-Z1-9]{25,34})|(bc1[a-zA-HJ-NP-Z0-9]{39,59})")

    def normalize_feature_name(self, name):
        """
        Helper to normalize names if needed (not strictly used if we rely on ModelLoader alignment).
        """
        return name

    def get_md5(self, file_path):
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return "N/A"

    def extract_features(self, file_path):
        """
        Extracts PE features from the given file path.
        Returns a dictionary suitable for DataFrame creation.
        """
        features = {}
        
        # 1. Metadata
        features['MD5'] = self.get_md5(file_path)
        
        try:
            pe = pefile.PE(file_path)
            
            # --- Header / Standard PE Features ---
            
            # Machine type (e.g., 332 for I386, 34404 for AMD64)
            features['Machine'] = pe.FILE_HEADER.Machine
            
            # Debug Size - usually summing up entries in debug directory
            debug_size = 0
            if hasattr(pe, 'DIRECTORY_ENTRY_DEBUG'):
                for entry in pe.DIRECTORY_ENTRY_DEBUG:
                    debug_size += entry.struct.SizeOfData
            features['DebugSize'] = debug_size

            # Image Version
            features['ImageVersion'] = pe.OPTIONAL_HEADER.MajorImageVersion

            # OS Version
            features['OSVersion'] = pe.OPTIONAL_HEADER.MajorOperatingSystemVersion

            # Linker Version
            features['LinkerVersion'] = pe.OPTIONAL_HEADER.MajorLinkerVersion

            # Number of Sections
            features['NumSections'] = pe.FILE_HEADER.NumberOfSections

            # Stack Size (SizeOfStackReserve or Commit? Usually Reserve)
            features['StackSize'] = pe.OPTIONAL_HEADER.SizeOfStackReserve

            # DLL Characteristics
            features['DLLCharacteristics'] = pe.OPTIONAL_HEADER.DllCharacteristics

            # Resource Size
            # Sum of sizes of all resources
            resource_size = 0
            if hasattr(pe, 'DIRECTORY_ENTRY_RESOURCE'):
                for resource_type in pe.DIRECTORY_ENTRY_RESOURCE.entries:
                    if hasattr(resource_type, 'directory'):
                        for resource_id in resource_type.directory.entries:
                            if hasattr(resource_id, 'directory'):
                                for resource_lang in resource_id.directory.entries:
                                    if hasattr(resource_lang, 'data'):
                                        resource_size += resource_lang.data.struct.Size
            features['ResourceSize'] = resource_size

            # --- String / Content Features ---
            
            # Bitcoin Addresses
            # Scan the whole file content? Or just data sections?
            # For simplicity and speed, we check extracted strings or raw data if small.
            # pefile provides get_memory_mapped_image()
            try:
                raw_data = pe.write() # Get raw bytes
                # Convert to string (ignoring errors) to run regex, or run bytes regex
                # Providing a boolean count or flag
                matches = self.btc_regex.findall(raw_data.decode(errors='ignore'))
                features['BitcoinAddresses'] = len(matches)
            except Exception:
                features['BitcoinAddresses'] = 0

            # Close PE file
            pe.close()

        except Exception as e:
            print(f"Error extracting features from {file_path}: {e}")
            # Return partial or empty features (ModelLoader will fill 0s)
            features['error'] = str(e)

        return features

    def get_features_df(self, file_path):
        """Returns a single-row DataFrame."""
        feat_dict = self.extract_features(file_path)
        # Drop non-numerical metadata (like MD5) if it's not a model feature, 
        # but keep it in the dict for display. ModelLoader separates alignment.
        return pd.DataFrame([feat_dict])
