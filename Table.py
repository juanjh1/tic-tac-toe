from Pices import VoidPice, Pice

class Table():
    SIZE = 3
    def __init__(self) -> None:
        self.__table  =  self.__generate_table(VoidPice)
       
    def __generate_table(self, void_pice: Pice) -> list[list[Pice]]:
        return [[ void_pice() for col in range(self.SIZE)] for row in range(self.SIZE)]
    def put_pice(self, x, y, pice) -> None:
        current_pice = self.__table[x][y]
        if  x<self.SIZE  and  y<self.SIZE and isinstance(current_pice,VoidPice):
            self.__table[x][y] = pice()

            
        
    def validate_pice(self,x,y)-> bool:
        return  not isinstance(self.__table[x][y], VoidPice)
    def validate_pice_oposite(self,x,y)-> bool:
        return   isinstance(self.__table[x][y], VoidPice)
    
    def get_image(self,x , y) :

        return self.__table[x][y].get_image()
    
    def print_table(self) -> None:
        print(self.__table)

    def validate_winner(self, pice) -> None:
        for fila in self.__table:
            if  all(isinstance(cell, pice) for cell in fila):
                 return True
        for col in range(self.SIZE):
            if all(isinstance(self.__table[fila][col], pice) for fila in range(self.SIZE)):
                return True
        if all(isinstance(self.__table[i][i], pice) for i in range(self.SIZE)):
            return True
        if all(isinstance(self.__table[i][self.SIZE - 1 - i], pice) for i in range(self.SIZE)):
            return True
        return False



if __name__ == "__main__":
    

    tb1 = Table()
    tb1.print_table()
