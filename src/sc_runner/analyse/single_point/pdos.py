import os
import json
import xml.etree.ElementTree as ET
import numpy as np


class PdosAnalyse:
    def __init__(self, pdosfile: str = './siesta.PDOS.xml') -> None:
        """
        Initialize the PdosAnalyse class.
        """
        self._pdosfile = pdosfile
        self._pdospath, self._pdosfilename = os.path.split(self._pdosfile)
        try:
            tree = ET.parse(self._pdosfile)
            self._root = tree.getroot()
        except (FileNotFoundError, ET.ParseError):
            raise ValueError('Invalid PDOS file or file not found.')

    @property
    def nspin(self) -> int:
        """
        Extract and cache the number of spins from the XML file.
        """
        element = self._root.find('nspin')
        if element is not None and element.text:
            return int(element.text.strip())
        raise ValueError('nspin not found or invalid in the XML file.')

    def extract_numeric_array(self, text: str) -> list:
        """
        Convert a string of space-separated numbers into a list of floats.
        """
        return [float(x) for x in text.split()] if text else []

    def extract_single_value(self, tag: str) -> float:
        """
        Extract a single numerical value from a specific XML tag.
        """
        element = self._root.find(tag)
        if element is not None and element.text:
            return float(element.text.strip())
        return None

    def extract_text(self, tag: str) -> str:
        """
        Extract text data from a specific XML tag.
        """
        element = self._root.find(tag)
        return element.text.strip() if element is not None else None

    def extract_orbital_data(self) -> list:
        """
        Extract detailed orbital data, including numerical values.
        """
        orbitals = []
        energy_values = self.extract_numeric_array(self._root.find('energy_values').text)
        energy_count = len(energy_values)

        for orbital in self._root.iter('orbital'):
            attributes = orbital.attrib  # Orbital metadata (species, atom_index, etc.)
            values = orbital[0].text if len(orbital) > 0 else ""  # Orbital numerical data
            orbital_data = self.extract_numeric_array(values)

            if len(orbital_data) != energy_count*self.nspin:
                raise ValueError(f"Mismatch in energy grid and orbital data for {attributes}")

            attributes['values'] = orbital_data  # Add numerical data to the attributes
            orbitals.append(attributes)

        return orbitals

    def generate_json(self) -> dict:
        """
        Generate a structured JSON object from the PDOS data.
        """
        pdos_data = {
            "nspin": self.nspin,
            "fermi_energy": self.extract_single_value("fermi_energy"),
            "energy_values": self.extract_numeric_array(self._root.find('energy_values').text),
            "orbitals": self.extract_orbital_data(),
        }
        return pdos_data

    def write_json(self, output_file: str) -> None:
        """
        Write the extracted PDOS data to a JSON file.
        """
        pdos_data = self.generate_json()
        with open(output_file, "w", encoding="utf-8") as json_file:
            json.dump(pdos_data, json_file, indent=4)
        print(f"JSON file written to {output_file}")


# Example usage:
if __name__ == "__main__":
    input_xml = './siesta.PDOS.xml'  # Replace with the path to your XML file
    output_json = './pdos_data.json'  # Path to save the JSON output

    analyser = PdosAnalyse(input_xml)
    analyser.write_json(output_json)

