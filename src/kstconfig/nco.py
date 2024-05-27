"""
Handling .nco files.

At EISCAT, these are loaded by the numerical controlled oscillator. These shift frequency of the signal 
that comes into a channel. When reading these files, one should be aware of that when the signal comes into the channels, its frequency already is shifted twice.

See also [Jussis EISCAT portal]
(https://portal.eiscat.se/jussi/eiscat/erosdoc/uhf_radar.html)
"""

class Nco:
    """Parsing and handling of numerically controlled oscillator (NCO) files.
    """
    def __init__(self, filename: str) -> None:
        """
        Initialie numerically controlled oscillator for single channel
        
        :param filename: Path to .nco file
        :type filename: str
        :raises ValueError: If file not has valid data.

        """
        self.freqs = []
        
        with open(filename) as file:
            lines = file.read()
            
        # First line MUST be NCOPAR_VS	0.1
        assert lines[0].split() == ["NCOPAR_VS", "0.1"]
        
        for il, line in enumerate(lines[1:]):
            text = line.split("%")[0]
            if text.isspace():
                continue
            elems = text.split()
            assert elems[0] == "NCO"
            nr = int(elems[1])
            assert nr == len(self.freqs)
            # Assert that elem[2] is a floatin.point number
            # If this works, this is the fastest way ... If not, it should crash anyway.
            # https://stackoverflow.com/questions/354038/how-do-i-check-if-a-string-represents-a-number-float-or-int/23639915#23639915
            try:
                freq = float(elems[2])
            except ValueError:
                msg = f"{elems[2]} in line{il+2} is not a valid number!"
                raise ValueError(msg)
            
            self.freqs.append(freq)

            
    def set_lo1(self, lo1: float) -> None:
        self._lo1 = lo1
    def set_lo2(self, lo2: float) -> None:
        self._lo2 = lo2
    def NCOSEL(self, nr: int) -> None:
        self.f_nco = self.freq[nr]
    def get_freq(self) -> float:
        return self.lo1 + self._lo2 + self.f_nco

            