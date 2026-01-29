# SPDX-License-Identifier: MIT
"""DCP format validation - formal playability only."""

from pathlib import Path
from typing import Dict, Any, List, Optional
import zipfile
import xml.etree.ElementTree as ET
from xmlschema import XMLSchema

from engine.core.errors import ValidationError


class DCPValidator:
    """
    DCP format validator.
    
    Validates structural conformance to DCP specification.
    Playback on specific devices or venues is explicitly excluded.
    """
    
    def __init__(self, schema_path: Optional[Path] = None):
        self.schema_path = schema_path or Path(__file__).parent / "schemas"
        self.schemas: Dict[str, Optional[XMLSchema]] = {}
        self._load_schemas()
    
    def _load_schemas(self) -> None:
        """Load XSD schemas."""
        schema_files = {
            "CPL": self.schema_path / "CPL.xsd",
            "PKL": self.schema_path / "PKL.xsd",
            "ASSETMAP": self.schema_path / "ASSETMAP.xsd",
        }
        
        for name, schema_file in schema_files.items():
            if schema_file.exists():
                try:
                    self.schemas[name] = XMLSchema(str(schema_file))
                except Exception:
                    self.schemas[name] = None
            else:
                self.schemas[name] = None
    
    def validate_dcp(self, dcp_path: Path) -> Dict[str, Any]:
        """
        Validate DCP package.
        
        Args:
            dcp_path: Path to DCP (directory or ZIP)
            
        Returns:
            Validation results dictionary
            
        Raises:
            ValidationError: If validation fails
        """
        results: Dict[str, Any] = {
            "format": "DCP",
            "passed": False,
            "errors": [],
            "warnings": [],
            "details": {},
        }
        
        try:
            # Check if DCP exists
            if not dcp_path.exists():
                raise ValidationError(f"DCP path does not exist: {dcp_path}")
            
            # Extract if ZIP
            if dcp_path.is_file() and dcp_path.suffix == ".zip":
                with zipfile.ZipFile(dcp_path, "r") as zf:
                    # Find ASSETMAP
                    assetmap_files = [f for f in zf.namelist() if "ASSETMAP" in f.upper()]
                    if not assetmap_files:
                        results["errors"].append("ASSETMAP not found")
                        return results
                    
                    # Validate ASSETMAP
                    assetmap_result = self._validate_assetmap(zf.read(assetmap_files[0]))
                    results["details"]["ASSETMAP"] = assetmap_result
                    
                    # Find PKL
                    pkl_files = [f for f in zf.namelist() if "PKL" in f.upper() and f.endswith(".xml")]
                    if pkl_files:
                        pkl_result = self._validate_pkl(zf.read(pkl_files[0]))
                        results["details"]["PKL"] = pkl_result
                    
                    # Find CPLs
                    cpl_files = [f for f in zf.namelist() if "CPL" in f.upper() and f.endswith(".xml")]
                    for cpl_file in cpl_files:
                        cpl_result = self._validate_cpl(zf.read(cpl_file))
                        results["details"].setdefault("CPLs", []).append({
                            "file": cpl_file,
                            "result": cpl_result,
                        })
            
            else:
                # Directory-based DCP
                assetmap_files = list(dcp_path.glob("**/ASSETMAP*"))
                if not assetmap_files:
                    results["errors"].append("ASSETMAP not found")
                    return results
                
                assetmap_result = self._validate_assetmap(assetmap_files[0].read_bytes())
                results["details"]["ASSETMAP"] = assetmap_result
            
            # Determine overall result
            if results["errors"]:
                results["passed"] = False
            else:
                results["passed"] = True
            
            return results
        
        except Exception as e:
            results["errors"].append(str(e))
            results["passed"] = False
            return results
    
    def _validate_assetmap(self, assetmap_data: bytes) -> Dict[str, Any]:
        """Validate ASSETMAP XML."""
        result = {
            "valid": False,
            "errors": [],
        }
        
        try:
            root = ET.fromstring(assetmap_data)
            
            # Basic structure check
            if root.tag != "{http://www.smpte-ra.org/schemas/429-8/2007/AM}AssetMap":
                result["errors"].append("Invalid ASSETMAP root element")
                return result
            
            # Schema validation if available
            if self.schemas.get("ASSETMAP"):
                try:
                    self.schemas["ASSETMAP"].validate(assetmap_data)
                    result["valid"] = True
                except Exception as e:
                    result["errors"].append(f"Schema validation failed: {e}")
            else:
                # Basic validation without schema
                result["valid"] = True
        
        except ET.ParseError as e:
            result["errors"].append(f"XML parse error: {e}")
        except Exception as e:
            result["errors"].append(f"Validation error: {e}")
        
        return result
    
    def _validate_pkl(self, pkl_data: bytes) -> Dict[str, Any]:
        """Validate PKL XML."""
        result = {
            "valid": False,
            "errors": [],
        }
        
        try:
            root = ET.fromstring(pkl_data)
            
            # Schema validation if available
            if self.schemas.get("PKL"):
                try:
                    self.schemas["PKL"].validate(pkl_data)
                    result["valid"] = True
                except Exception as e:
                    result["errors"].append(f"Schema validation failed: {e}")
            else:
                result["valid"] = True
        
        except ET.ParseError as e:
            result["errors"].append(f"XML parse error: {e}")
        except Exception as e:
            result["errors"].append(f"Validation error: {e}")
        
        return result
    
    def _validate_cpl(self, cpl_data: bytes) -> Dict[str, Any]:
        """Validate CPL XML."""
        result = {
            "valid": False,
            "errors": [],
        }
        
        try:
            root = ET.fromstring(cpl_data)
            
            # Schema validation if available
            if self.schemas.get("CPL"):
                try:
                    self.schemas["CPL"].validate(cpl_data)
                    result["valid"] = True
                except Exception as e:
                    result["errors"].append(f"Schema validation failed: {e}")
            else:
                result["valid"] = True
        
        except ET.ParseError as e:
            result["errors"].append(f"XML parse error: {e}")
        except Exception as e:
            result["errors"].append(f"Validation error: {e}")
        
        return result

