"""
Molecular analysis module for NMR spectrum prediction from InChI.
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class EnvironmentPrediction:
    """Predicted NMR environment for a molecular fragment."""
    atom_type: str
    predicted_shift: float
    confidence: float
    environment_description: str
    predicted_multiplicity: str
    predicted_integration: int

class MolecularAnalyzer:
    """Analyze molecular structure from InChI and predict NMR parameters."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.rdkit_available = self._check_rdkit()
        
    def _check_rdkit(self) -> bool:
        """Check if RDKit is available."""
        try:
            from rdkit import Chem
            return True
        except ImportError:
            self.logger.warning("RDKit not available. Install with: conda install -c conda-forge rdkit")
            return False
    
    def analyze_inchi(self, inchi: str, nucleus: str = "1H") -> List[EnvironmentPrediction]:
        """
        Analyze InChI and predict NMR environments.
        
        Args:
            inchi: InChI string of the molecule
            nucleus: NMR nucleus ("1H" or "13C")
            
        Returns:
            List of predicted NMR environments
        """
        if not self.rdkit_available:
            return self._fallback_analysis(inchi, nucleus)
        
        try:
            from rdkit import Chem
            from rdkit.Chem import Descriptors
            
            # Convert InChI to molecule
            mol = Chem.MolFromInchi(inchi)
            if mol is None:
                self.logger.error(f"Failed to parse InChI: {inchi}")
                return self._fallback_analysis(inchi, nucleus)
            
            # Analyze based on nucleus
            if nucleus == "1H":
                return self._analyze_protons(mol)
            elif nucleus == "13C":
                return self._analyze_carbons(mol)
            else:
                self.logger.warning(f"Unsupported nucleus: {nucleus}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error analyzing InChI: {e}")
            return self._fallback_analysis(inchi, nucleus)
    
    def _analyze_protons(self, mol) -> List[EnvironmentPrediction]:
        """Analyze proton environments in molecule."""
        from rdkit import Chem
        
        predictions = []
        
        # Get all hydrogen-bearing carbons
        for atom in mol.GetAtoms():
            if atom.GetSymbol() == 'C':
                # Count attached hydrogens
                num_h = atom.GetTotalNumHs()
                if num_h == 0:
                    continue
                
                # Predict chemical shift based on environment
                shift = self._predict_carbon_h_shift(atom, mol)
                multiplicity = self._predict_multiplicity(atom, mol)
                
                # Create environment description
                env_desc = self._describe_carbon_environment(atom, mol)
                
                prediction = EnvironmentPrediction(
                    atom_type="H",
                    predicted_shift=shift,
                    confidence=0.7,  # Moderate confidence for heuristic predictions
                    environment_description=env_desc,
                    predicted_multiplicity=multiplicity,
                    predicted_integration=num_h
                )
                predictions.append(prediction)
        
        return predictions
    
    def _analyze_carbons(self, mol) -> List[EnvironmentPrediction]:
        """Analyze carbon environments in molecule."""
        predictions = []
        
        for atom in mol.GetAtoms():
            if atom.GetSymbol() == 'C':
                shift = self._predict_carbon_shift(atom, mol)
                env_desc = self._describe_carbon_environment(atom, mol)
                
                prediction = EnvironmentPrediction(
                    atom_type="C",
                    predicted_shift=shift,
                    confidence=0.6,
                    environment_description=env_desc,
                    predicted_multiplicity="s",  # Most carbons appear as singlets in 13C
                    predicted_integration=1
                )
                predictions.append(prediction)
        
        return predictions
    
    def _predict_carbon_h_shift(self, carbon_atom, mol) -> float:
        """Predict 1H chemical shift for protons on a carbon."""
        from rdkit import Chem
        
        # Base shift for alkyl CH
        base_shift = 0.9
        
        # Check for aromatic carbons
        if carbon_atom.GetIsAromatic():
            return 7.2 + (hash(str(carbon_atom.GetIdx())) % 100) / 500.0  # 7.0-7.4 ppm range
        
        # Check neighbors for deshielding effects
        for neighbor in carbon_atom.GetNeighbors():
            if neighbor.GetSymbol() == 'O':
                base_shift += 2.5  # Oxygen deshielding
            elif neighbor.GetSymbol() == 'N':
                base_shift += 1.5  # Nitrogen deshielding
            elif neighbor.GetIsAromatic():
                base_shift += 1.8  # Aromatic deshielding
        
        # Add some variation based on position
        variation = (hash(str(carbon_atom.GetIdx())) % 50) / 100.0
        return base_shift + variation
    
    def _predict_carbon_shift(self, carbon_atom, mol) -> float:
        """Predict 13C chemical shift."""
        base_shift = 20.0  # Base alkyl carbon
        
        if carbon_atom.GetIsAromatic():
            return 128.0 + (hash(str(carbon_atom.GetIdx())) % 100) / 5.0  # 120-140 ppm
        
        # Adjust based on hybridization and neighbors
        if carbon_atom.GetHybridization().name == 'SP2':
            base_shift += 100.0  # Alkene carbons ~120 ppm
        
        for neighbor in carbon_atom.GetNeighbors():
            if neighbor.GetSymbol() == 'O':
                base_shift += 50.0
            elif neighbor.GetSymbol() == 'N':
                base_shift += 30.0
        
        variation = (hash(str(carbon_atom.GetIdx())) % 50) / 2.0
        return base_shift + variation
    
    def _predict_multiplicity(self, carbon_atom, mol) -> str:
        """Predict multiplicity based on neighboring carbons."""
        from rdkit import Chem
        
        # Count neighboring carbons with hydrogens
        neighboring_h_count = 0
        for neighbor in carbon_atom.GetNeighbors():
            if neighbor.GetSymbol() == 'C':
                neighboring_h_count += neighbor.GetTotalNumHs()
        
        # Simplified J-coupling prediction
        if neighboring_h_count == 0:
            return "s"  # singlet
        elif neighboring_h_count == 1:
            return "d"  # doublet
        elif neighboring_h_count == 2:
            return "t"  # triplet
        elif neighboring_h_count == 3:
            return "q"  # quartet
        else:
            return "m"  # multiplet
    
    def _describe_carbon_environment(self, atom, mol) -> str:
        """Generate description of carbon environment."""
        if atom.GetIsAromatic():
            return "Aromatic CH"
        
        num_h = atom.GetTotalNumHs()
        if num_h == 3:
            return "Methyl"
        elif num_h == 2:
            return "Methylene"
        elif num_h == 1:
            return "Methine"
        else:
            return "Quaternary carbon"
    
    def _fallback_analysis(self, inchi: str, nucleus: str) -> List[EnvironmentPrediction]:
        """Fallback analysis when RDKit is not available."""
        self.logger.info("Using fallback molecular analysis (limited accuracy)")
        
        # Simple heuristic based on InChI content
        predictions = []
        
        if nucleus == "1H":
            # Look for common patterns in InChI
            if "c1ccccc1" in inchi.lower():  # Benzene ring
                predictions.append(EnvironmentPrediction(
                    atom_type="H",
                    predicted_shift=7.25,
                    confidence=0.5,
                    environment_description="Aromatic protons (predicted)",
                    predicted_multiplicity="m",
                    predicted_integration=5
                ))
            
            if "CH3" in inchi:
                predictions.append(EnvironmentPrediction(
                    atom_type="H",
                    predicted_shift=1.2,
                    confidence=0.4,
                    environment_description="Methyl protons (predicted)",
                    predicted_multiplicity="s",
                    predicted_integration=3
                ))
        
        if not predictions:
            # Default prediction
            default_shift = 7.2 if nucleus == "1H" else 128.0
            predictions.append(EnvironmentPrediction(
                atom_type=nucleus.replace("1", ""),
                predicted_shift=default_shift,
                confidence=0.3,
                environment_description="Unknown environment (install RDKit for better analysis)",
                predicted_multiplicity="s",
                predicted_integration=1
            ))
        
        return predictions
    
    def enhance_peak_data(self, peak_data: List[Dict], inchi: str, nucleus: str) -> List[Dict]:
        """
        Enhance experimental peak data with structural predictions.
        
        Args:
            peak_data: List of experimental peak dictionaries
            inchi: InChI string for structural context
            nucleus: NMR nucleus
            
        Returns:
            Enhanced peak data with structural assignments
        """
        if not inchi:
            return peak_data
        
        # Get structural predictions
        predictions = self.analyze_inchi(inchi, nucleus)
        
        # Try to match experimental peaks with predictions
        enhanced_peaks = []
        for peak in peak_data:
            enhanced_peak = peak.copy()
            
            # Find closest prediction
            closest_prediction = None
            min_diff = float('inf')
            
            for pred in predictions:
                diff = abs(pred.predicted_shift - peak['shift'])
                if diff < min_diff:
                    min_diff = diff
                    closest_prediction = pred
            
            # Add structural information if match is reasonable
            if closest_prediction and min_diff < 2.0:  # Within 2 ppm
                enhanced_peak['structural_assignment'] = closest_prediction.environment_description
                enhanced_peak['prediction_confidence'] = closest_prediction.confidence
                
                # Use predicted integration if experimental is missing/poor
                if peak.get('integration', 0) <= 0:
                    enhanced_peak['integration'] = closest_prediction.predicted_integration
                
                # Use predicted multiplicity if missing
                if not peak.get('multiplicity') or peak['multiplicity'] == 'm':
                    enhanced_peak['multiplicity'] = closest_prediction.predicted_multiplicity
            
            enhanced_peaks.append(enhanced_peak)
        
        self.logger.info(f"Enhanced {len(enhanced_peaks)} peaks with structural predictions")
        return enhanced_peaks

# Global analyzer instance
molecular_analyzer = MolecularAnalyzer()
