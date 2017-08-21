import scard
import xktool
import time


"""
command read:
[0] 00 A4 00 00 02 21 01
[0] 00 B0 00 00 0a 
"""
FILE_USERNAME = 0x01
FILE_PASSWORD = 0x02
FILE_SIZE     = 128

SELECT_DF = 0x10 
SELECT_EF = 0x01

cmd_select_file   = [0x00,0xA4,0x00,0x00,0x02]
cmd_get_response  = [0x00,0xC0,0x00,0x00]
cmd_read_data     = [0x00,0xB0,0x00,0x00]

def select_file(con,filetype,filenum):
    if(filetype==SELECT_DF):
        resp = con.transceive(bytearray(cmd_select_file + [SELECT_DF,0x01]))
    else:
        resp = con.transceive(bytearray(cmd_select_file + [SELECT_EF,filenum]))
    status = xktool.get_response_status(resp)
    if(status>>8 == 0x61):
        return status
    else:
        return None 
        
def get_file_setting(con,status):
    filesetlen =  status & 0xFF
    resp = con.transceive(bytearray(cmd_get_response + [filesetlen]))
    status = xktool.get_response_status(resp)
    if(status == 0x9000):
        lsfileset = xktool.get_response_data()    
        return lsfileset
    else:
        return None
    
def get_file_size(lsfileset):
    filesize = (lsfileset[17] << 8) | lsfileset[18]
    return filesize 
    
def read_data(con,filesize):
    resp = con.transceive(bytearray(cmd_read_data + [filesize]))
    status = xktool.get_response_status(resp)
    if(status == 0x9000):
        lsdata = xktool.get_response_data(resp)
        for i in range(len(lsdata)):
            if(lsdata[i] == 0x00):
                 return lsdata[:i]
    else:
        return None

    

def init():
    ctx=scard.context()
    con=ctx.connector(0)
    xktool.waittoconnect(con)
    con.connect()
    return con
    
    
""" 
API
- Call Function  : get_scard_login()
- Output success : dict = {'Username': 'username',
                           'Password': 'password'}
- Output error   : None                        
"""
def get_scard_login():

    ctx=scard.context()
    con=ctx.connector(0)
    xktool.waittoconnect(con)
    # time.sleep(7)
    con.connect()
    
    dict = {}

    status = select_file(con,SELECT_DF,0x01)
    if(status == None):
        return None
    status = select_file(con,SELECT_EF,FILE_USERNAME)
    if(status == None):
        return None         
    lsusername = read_data(con,FILE_SIZE)
    if(lsusername == None):
        return None
    status = select_file(con,SELECT_EF,FILE_PASSWORD)
    if(status == None):
        return None
    lspassword = read_data(con,FILE_SIZE)
    if(lspassword == None):
        return None
    

    b_username = xktool.list2byte(lsusername)
    s_username = b_username.decode()
    b_password = xktool.list2byte(lspassword)
    s_password = b_password.decode()
    
    dict['Username'] = s_username; 
    dict['Password'] = s_password;

    con.disconnect()
    return dict

    


    
