import json
from pathlib import Path

class Detakon():
    """detakon uses a detakon map to convert data."""
    def __init__(self, detamap, source, destination, sdtype: str="csv", ddtype: str="csv", *args, **kargs):
        """
        Initialize all values for Detakon object.
        
        :param self: Object reference.
        :param detamap: detamap location that describes field mappings, default values, and operations to perform on data.
        :param source: Source to input.
        :param destination: Destination to output.
        :param sdtype: Source data format type. Defaults to CSV.
        :type sdtype: str
        :param ddtype: Destination data format type. Defaults to CSV.
        :type ddtype: str
        :param args: Additional parameters.
        :param kargs: Addtional flags.
        """
        self.detamap = self.load_detamap(detamap)
        self.source = self.load_source_string(source) # see note in method pass

    def load_source_string(self, source) -> str:
        """
        Validate source as file path, and return as string.
        
        :param self: Object reference.
        :param source: File path.
        :return: File path as string.
        :rtype: str
        """
        # Thoughts: Accept file or generator object reference - rely on caller to supply data stream if not a file.
        pass # Halted development - reconsideration for how to additionally accept non-file streams

    def load_detamap(self, detamap) -> dict:
        """
        Process object passed as detamap and return dictionary detamap.
        
        :param self: Object reference.
        :param detamap: Either a dictionary, JSON stream/string, or file path (string or pathlib.Path) to JSON file.
        :return: Dictionary of detamap
        :rtype: dict
        """
        if isinstance(detamap, dict):
            return detamap
        elif isinstance(detamap, str) and detamap[0] == '{':
            try:
                return json.loads(detamap)
            except Exception as e:
                raise Exception(f"Failed to load JSON string: {e}")
        else:
            try:
                if isinstance(detamap, Path):
                    with detamap.open("r") as file:
                        return json.load(file)
                else:
                    with open(detamap, "r") as file:
                        return json.load(file)
            except Exception as e:
                raise Exception(f"Failed to load JSON file: {e}")
        