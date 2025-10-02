from assets_loader import XPICE_IMG, OPICE_IMG


class Pice():
    
    def __init__(self, symbol: str, img= None) -> None:
        self.symbol = symbol
        self.img = img

    def __str__(self) -> str:
        return self.symbol
    def __repr__(self) -> str:
        return self.symbol
  
    def get_image(self):
        return self.img


class XPice(Pice) :

    def __init__(self):
        super().__init__("X", XPICE_IMG)
    




class OPice(Pice):

    def __init__(self):
        super().__init__("O", OPICE_IMG)
         


class VoidPice(Pice):

    def __init__(self, ):
        super().__init__("-")

    
         