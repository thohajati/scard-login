import SCardLogin

if __name__ == '__main__':
    
    dict = {}    
    print("Insert your card!")
    dict = SCardLogin.get_scard_login()    
    print(str(dict))
 
            
    
            
    
    
    
    
    
    