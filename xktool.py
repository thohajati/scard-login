# Table CRC32 akan diiisi saat pemanggilan crc32 pertamakali'
import scard
import time
#import config as CONFIG

_tablecrc32 = list()

class ReadError(Exception):
    def __init__(self,msg,addr,value):
        super(ReadErrorException,self).__init__(msg)
        self.__addr__ = addr
        self.__value__ = value

    def get_addr(self):
        return self.__addr__
    
    def get_value(self):
        return self.__value__


class WriteErrorException(Exception):
    def __init__(self,msg,addr,val,banknum):
        super(WriteError,self).__init__(msg)
        self.__addr__ = addr
        self.__value__ = val
        self.__banknum__ = banknum

    def get_value(self):
        return self.__value__

    def get_addr(self):
        return self.__addr__

    def get_banknum(self):
        return self.__banknum__

        
class APDUError(Exception):
    def __init__(self,msg,apdu,status,expected):
        super(APDUError,self).__init__(msg)
        self.__apdu__ = apdu
        self.__status__ = status
        self.__expected__ = expected            
        
    def get_apdu(self):
        return self.__apdu__
            
    def get_status(self):
        return self.__status__
        
    def get_expected(self):
        return self.__expected__            


class EraseAllErr(APDUError):
    def __init__(self,apdu,status,expected):
        super(EraseAllErr,self).__init__("Erase All Error",apdu,status,expected)


class SelectBankErr(APDUError):
    def __init__(self,apdu,status,expected,banknum):
        super(SelectBankErr,self).__init__("Select Bank Error",apdu,status,expected)
        self.__bnknum__ = banknum

        
    def get_banknum(self):
        return self.__banknum__


        
class AnimateProcess:
    def __init__(self,szprocname):
        self.__szproc__ = szprocname
        self.__counter__ = 0
        self.__animap__ = {0: '|', 1:'/', 2:'-', 3:'\\'}
    
    def __exit__(self,type,value,traceback):
        self.end()
        
        
    def begin(self):
        print(self.__szproc__ + ":   ",end="",flush=True)


    def animate(self):
        print('\x08',end="",flush=True)
        print("%s" % self.__animap__[self.__counter__],end="",flush=True)
        self.__counter__ +=1
        if(self.__counter__ == 4):
            self.__counter__ = 0
        

    def end(self):
        for x in range(3):
            print("\x08",end="",flush=True)
        print(" FINISHED")
        
        
        
def erase_all(con):
    payload = bytearray([0x51,0x02,0x00,0x00,0x01,0xff])
    resp = con.transceive(payload)
    if(get_response_status(resp) != 0x9000):
        raise EraseAllErr(payload,get_response_status(resp),0x9000)



def erase_sector(con,sector):
    sctmsb = (sector>>8) & 0xff
    sctlsb = sector & 0xff
    payload = bytearray([0x51,0x02,0x00,0x00,0x02,sctmsb,sctlsb])
    resp = con.transceive(payload)
    status = get_response_status(resp)
    if( status != 0x9000):
        raise APDUError("Erase Sector's Error",payload,status,0x9000)

        
def select_bank(con,number):
    payload = bytearray([0x51,0x06,0x00,0x00,0x01,number])
    resp = con.transceive(payload)
    if(get_response_status(resp) != 0x9000):
        raise SelectBankErr(payload,get_response_status(resp),0x9000,number)

        
"""
Blocking until theres "connected" state on card reader
"""
def waittoconnect(con):
    while(1):
        state = con.readerstate()
        if(state.eventstate & scard.SCARD_STATE_INUSE):
            #DON'T PUT sleep in here just continue the loop!!
            continue
        if(state.eventstate & scard.SCARD_STATE_PRESENT):
            break
    time.sleep(0.5)
    
    
"""
Blocking until there is "disconnected" state on card reader
"""
def waittodisconnect(con):
    while(1):
        state = con.readerstate()
        if(state.eventstate & scard.SCARD_STATE_INUSE):
            #DON'T PUT sleep in here just continue the loop!!
            continue
        if(state.eventstate & scard.SCARD_STATE_EMPTY):
            break
    time.sleep(0.5)
    
    
def get_response_status(lsresp):
    if(isinstance(lsresp,bytes) == False):
        raise TypeError("Input should be list of bytes")
    if(len(lsresp) < 2):
        raise RuntimeError("Length input too little")
        
    return int("".join("%2.2x" % c for c in lsresp[len(lsresp)-2:]),16)

    
def get_response_data(lsresp):
    if(isinstance(lsresp,bytes) == False):
        raise TypeError("Input should be list of bytes")
    if(len(lsresp) < 2):
        raise RuntimeError("Length input too little")
        
    return lsresp[0:len(lsresp)-2]   

    
def list2int(lsresp):         
    return int("".join("%2.2x" % c for c in lsresp),16)

    
def list2byte(lsresp):
    respint = int("".join("%2.2x" % c for c in lsresp),16)
    return respint.to_bytes(len(lsresp),'big')

    
def list2str(lsinp):
    szinp = ""
    for i in lsinp:
        szinp = szinp + ("%2.2x" % i)
    return szinp

    
def byte2str(input):
    lsinp = memoryview(input).tolist()
    szinp = ""
    for i in lsinp:
        szinp = szinp + ("%2.2x" % i)
    return szinp

    
def str2byte(str):  
    strlist = [str[i:i+2] for i in range(0,len(str), 2)]
    intlist = [int(x, 16) for x in strlist] 
    return list2byte(intlist)

    
def str2list(str):  
    strlist = [str[i:i+2] for i in range(0,len(str), 2)]
    return [int(x, 16) for x in strlist]    
    

    
"""
    Argumen (args):
        rangkaian tuple dengan format judul-listoflistdata, rangkaian argumen
        bisa beberapa tuple atau tidak ada tuple sama sekali (lihat contoh)
        
    Keyword-argument(kwargs):
        PRINTCMD='yes'
            berarti di file output akan ditulis command yang dikirim ke board. Jika keyword ini
            tidak ada maka secara default fungsi tidak akan menulis command2 yang dikirim ke board
            
        RESULT=<data list>
            Berarti data list diatas akan dianggap sebagai hasil perhitungan di board dan ditulis ke file
            output
            
            
    Contoh penggunaan fungsi:
    
    lsa=[[1,2,3,4,5,6,7],[1,2,3,4,5,6,7],[1,2,3,4,5,6,7],[1,2,3,4,5,6,7],[1,2,3,4,5,6,7]]
    lsb=[[2,3,4,5,6,0,2,1],[2,3,4,5,6,0,2,1],[2,3,4,5,6,0,2,1],[2,3,4,5,6,0,2,1],[2,3,4,5,6,0,2,1]]
    lsc=[[5,6,7,8,9,2,3,4,5,6],[5,6,7,8,9,2,3,4,5,6]]
    lsres=[1,2,3,4,5,6,7,8,7,6,5,4,3,2]
    dumptofile('testtest.txt',('Operand 1',lsa),('Operand 2',lsb),('Operand 3',lsc),PRINTCMD='yes',RESULT=lsres)    
"""
def dumptofile(szfname,*args,**kwargs):
    fname = open(szfname,'a+')
    fname.write('<==================== BEGIN ====================\n\n')
    for i in args:
        fname.write('------------ %s ------------\n' % i[0])
        for ls in i[1]:
            szdata = ":".join("%2.2X" % c for c in ls[5:])
            fname.write(szdata+'\n')
            
    if('RESULT' in kwargs):
        fname.write('\n------------ BOARD RESULT ------------\n')
        fname.write("".join("%2.2X" % c for c in kwargs['RESULT'])+'\n')

    if('PRINTCMD' in kwargs):
        if(kwargs['PRINTCMD']=='yes'):
            fname.write("\n==================\nBOARD COMMAND\n==================\n")
            for i in args:
                for ls in i[1]:
                    fname.write("".join("%2.2X" % c for c in ls)+'\n')
    fname.write('\n==================== END ====================>\n\n\n\n\n')

"""
    Menghitung crc16 ISO 7816
    Input: [data list yang akan dihitung crcnya] + [crc init msb] + [crc init lsb]
    Output: nilai crc dari input (integer)
"""    
def crc16_iso7816(input):

    crchighbit    = 0x8000;
    crcinit       = 0xFFFF;
    crcpolynom    = 0x1021;
    
    initmsb = input[len(input)-2]
    initlsb = input[len(input)-1]
    
    crc = (initmsb << 8) | initlsb
    print("crc init: %4.4x" % crc)
    for i in range(0,len(input)-2):
        j = 0x80
        while(j >= 1):
            bit = crc & crchighbit
            crc <<= 1
            if(input[i] & j):
                bit ^= crchighbit
            if(bit):
                crc ^= crcpolynom
            j >>= 1
    
    return crc
        
"""    
    Menghitung crc16 ISO 14443, 
    input ada list of byte yang akan dihitung CRC-nya
    return value adalah crc dengan list of 2 byte  atau None jika gagal
"""
def crc16_ex(lsinput):
    crcval = 0x6363;
    for ubyte in lsinput:
        ch = (ubyte ^ (crcval)) & 0xFF
        ch = (ch ^ (ch << 4)) & 0xFF
        crcval = ((crcval >> 8) ^( ch << 8)  ^ ( ch << 3) ^ (ch>>4)) & 0xFFFF        
    return memoryview(crcval.to_bytes(2,'little')).tolist()
    
"""    
    Menghitung crc16 contact, 
    input ada list of byte yang akan dihitung CRC-nya
    return value adalah crc dengan list of 2 byte  atau None jika gagal
"""
def crc16(lsinput):
    crcval = 0x6363;
    for ubyte in lsinput:
        ch = (ubyte ^ (crcval)) & 0xFF
        ch = (ch ^ (ch << 4)) & 0xFF
        crcval = ((crcval >> 8) ^( ch << 8)  ^ ( ch << 3) ^ (ch>>4)) & 0xFFFF        
    return memoryview(crcval.to_bytes(2,'big')).tolist()
    
    
"""
    partisi menjadi listdata berukuran besar menjadi beberapa list dengan panjang maximum per-list adalah 32 byte
    incmd   = input command/inst command
    lsdata  = list data input
    
    NOTE:
        Parameter CLA di-hardcoded menjadi 0x51
"""
def partition_data(incmd,lsdata,init_offset,maxdata):    
    lsres = list()    
    offset = init_offset
    while(offset < (len(lsdata)+init_offset)):
        ls=list()
        ls.extend([0x51,incmd])
        ls.extend(memoryview(offset.to_bytes(2,'big')).tolist())
        ilen = len(lsdata) - (offset-init_offset)
        if(ilen > maxdata):
            ilen = maxdata
        ls.append(ilen)
        ls.extend(lsdata[(offset-init_offset):(offset-init_offset+maxdata)])
        lsres.append(ls)
        offset=offset+ilen
    return lsres     
    

"""
Fungsi menghitung CRC32
    Input: List of byte
    Output: list of 4 byes of crc32
"""
def crc32(lsdatain):
    if (isinstance(lsdatain,list) == False):
        raise TypeError('Input type should be list of byte')

    if(len(_tablecrc32) == 0):
        for n in range(256) :
            c = n
            for k in range(8):
                if( c & 0x01):
                    c = 0xEDB88320 ^ (c >> 1)
                else:
                    c = c >> 1
                    
            _tablecrc32.append(c & 0xFFFFFFFF)
    crc = 0xFFFFFFFF
    for i in lsdatain:
        crc = _tablecrc32[(crc ^ i) & 0xFF] ^ (crc >> 8);
        crc = crc & 0xFFFFFFFF

    
    return memoryview(crc.to_bytes(4,'little')).tolist()

"""
Fungsi megirim list apdu
"""    
def sendingstreamdata(conn,listofdata):
    for partition in listofdata:
        resp=con.transceive(partition)
        if(resp[0] != 0x9000):
            print("Gagal mengirim data, ret=0x%4.4X" % resp[0])
            return -1
            
    return 0

    
def generatemod(sizemod):
    retval=int()
    while True:
        retval = random.getrandbits(sizemod)
        if((retval % 2) == 1):
            break
    return retval

    
def get_random_list(bsize):
    random.seed(datetime.datetime.now().microsecond)
    mod = generatemod(bsize)
    a   = random.getrandbits(bsize)
    b   = random.getrandbits(bsize)    
    r2  =((2**((bsize+2)*2)) % mod)    
    valid = pow(a,b,mod)
    list_a          = memoryview(a.to_bytes(bsize//8,'big')).tolist()
    list_b          = memoryview(b.to_bytes(bsize//8,'big')).tolist()
    list_m          = memoryview(mod.to_bytes(bsize//8,'big')).tolist()
    listr2          = memoryview(r2.to_bytes(bsize//8,'big')).tolist()
    list_expect     = memoryview(valid.to_bytes((bsize//8)+2,'big')).tolist()
    return (list_a,list_b,listr2,list_m,list_expect)

    
def dumpfail(szfname,apdu,resp_status):
    fname = open(szfname,'a+')    
    fname.write('- APDU          : %s\n' % apdu)
    fname.write('- FAIL Code     : 0x%X\n' % resp_status)
    fname.write('\n')

    
def dec2hex(lsdec):
    szdata=str()
    for i in lsdec:
        szdata=szdata + " " + str("%2.2X" % i)
    
    return szdata
    

def write_flash(con,banknum,apdulist,FILENAME):
    
    # Select Bank 
    apdu = [0x51,0x24,0x00,0x00,0x01,banknum]
    lsresp=con.transceive(apdu) 
    
    if(get_response_status(lsresp) !=0x9000):
        szdata=str()
        for i in apdu:
            szdata=szdata + " " + str("%2.2X" % i)
        dumpfail(FILENAME,szdata,resp[0])
        if (resp[0] == 0x6300):
            con.disconnect()
            while(con.connect() !=0):
                print("try connect")
        return 1
    
            
    # Erase Flash
    addr = (apdulist[0][2] << 8 | apdulist[0][3])        
    
    if(banknum == 0):
        sector = (addr>>11)
    elif(banknum == 1):
        sector = (addr>>11)
    elif(banknum == 2):
        sector = (addr>>11) + 1*(0x8000>>11)
    elif(banknum == 3):
        sector = (addr>>11) + 2*(0x8000>>11)
    elif(banknum == 4):
        sector = (addr>>11) + 3*(0x8000>>11)
    elif(banknum == 5):
        sector = (addr>>11) + 4*(0x8000>>11)
    else:
        raise RuntimeError("bank number should be less than 5") 
    
    
    apdu = [0x51,0x23,0x00,0x00,0x01,sector]
    lsresp=con.transceive(apdu)
                
    if(get_response_status(lsresp) !=0x9000):
        szdata=str()
        for i in apdu:
            szdata=szdata + " " + str("%2.2X" % i)              
        dumpfail(FILENAME,szdata,resp[0])
        
        if (resp[0] == 0x6300):
            con.disconnect()
            while(con.connect() !=0):
                print("try connect")                
        return 1
        
    
    
    for partition in apdulist:              
        
        # check offset, apabila melintasi batas sector maka harus sector erase terlebuh dahulu sebelum write flash
        P1 = partition[2]
        P2 = partition[3]
        addr = (P1 << 8) | P2
        
        if(banknum == 0):
            sector = (addr>>11)
        elif(banknum == 1):
            sector = (addr>>11)
        elif(banknum == 2):
            sector = (addr>>11) + 1*(0x8000>>11)
        elif(banknum == 3):
            sector = (addr>>11) + 2*(0x8000>>11)
        elif(banknum == 4):
            sector = (addr>>11) + 3*(0x8000>>11)
        elif(banknum == 5):
            sector = (addr>>11) + 4*(0x8000>>11)
        else:
            raise RuntimeError("bank number should be less than 5")
                    
        if(addr % 2048 == 0):
            apdu = [0x51,0x23,0x00,0x00,0x01,sector]
            lsresp=con.transceive(apdu)
                
            if(get_response_status(lsresp) !=0x9000):
                szdata=str()
                for i in apdu:
                    szdata=szdata + " " + str("%2.2X" % i)              
                dumpfail(FILENAME,szdata,resp[0])
                
                if (resp[0] == 0x6300):
                    con.disconnect()
                    while(con.connect() !=0):
                        print("try connect")                
                return 1
                
        # Write Flash               
        lsresp=con.transceive(partition)
        print(".",end="",flush=True)
                
        if((get_response_status(lsresp) !=0x9000) & (get_response_status(lsresp) != 0x6300)):
            szdata=str()        
            for i in partition:
                szdata=szdata + " " + str("%2.2X" % i)          
                
            dumpfail(FILENAME,szdata,resp[0])
            return 1
        
        try_cnt=0   
        while (get_response_status(lsresp) == 0x6300):
            con.disconnect()
            while(con.connect() !=0):
                print("try connect")
            
            if(try_cnt < 4):
                try_cnt +=1
                lsresp=con.transceive(partition)
                print(".",end="",flush=True)
                if((get_response_status(lsresp) !=0x9000) & (get_response_status(lsresp) != 0x6300)):
                    szdata=str()
                    for i in apdu:
                        szdata=szdata + " " + str("%2.2X" % i)              
                    dumpfail(FILENAME,szdata,resp[0])
                    return 1    
    
    return 0
    
    
def read_flash():
    data = [] #reset data write
    
    ############### Select Bank #################
    apdu = [0x51,0x24,0x00,0x00,0x01,banknum]
    resp=con.transceive(apdu)
    print("")
    print("Select Bank %d" % banknum)
    szdata=str()
    for i in apdu:
        szdata=szdata + " " + str("%2.2X" % i)
    print("apdu = ",szdata)
    print("resp->status = 0x%X" % (resp[0]))
    szdata=str()
    for i in resp[1]:
        szdata=szdata + " " + str("%2.2X" % i)
    print("resp->data = ",szdata)
    print("")   
        
    ############## Read Flash ###################
    apdu=[0x51,0x22,P1,P2,WRITEDATANUM]
    ls=con.transceive(apdu)
    print("Read Flash %d Bytes" % WRITEDATANUM)
    for i in apdu:
        szdata=szdata + " " + str("%2.2X" % i)
    print("apdu = ",szdata)
    print("resp->status = 0x%X" % (ls[0]))
    szdata=str()
    for i in ls[1]:
        szdata=szdata + " " + str("%2.2X" % i)
    print("resp->data = ",szdata)
    print("")


def write_cell(con,addr,val):       
    
    if(addr > (0x21ffe+0x8000)):
        raise RuntimeError("Cann't write at address > 0x21ffe")
        
    # write cell
    msbaddr = (addr >> 8) & 0xff
    lsbaddr = addr & 0xff
    
    return con.transceive(bytearray([0x51,0x07,msbaddr,lsbaddr,0x01,val]))
    
    
def read_cell(con,addr):

    if(addr > (0x21ffe+0x8000)):
        raise RuntimeError("Cann't read at address > 0x21ffe")
            
    # read cell
    msbaddr = (addr >> 8) & 0xff
    lsbaddr = addr & 0xff
    resp = con.transceive(bytearray([0x51,0x04,msbaddr,lsbaddr,0x01]))
    return memoryview(get_response_data(resp)).tolist()[0]
    
    
"""
    Merubah payload menjadi string untuk ditulis ke terminal ataupun ke logfile
    kwargs:
        lenblock = [Integer]
            The length of data string in a line
        
        enableaddr = [Boolean True/False]
            Enable the address information on string returned value
            
        startaddr = [Integer] 
            Starting address of the payload
"""
def payload2str(pdu,**kwargs):
    lenblock=16
    addr = 0x0000
    enaddr = True
    
    if "lenblock" in kwargs:
        if isinstance(kwargs["lenblock"],int) == False:
            raise TypeError("lenblock should be boolean type ( True/False )")
        lenblock=kwargs["lenblock"]
        
    if "startaddr" in kwargs:
        if isinstance(kwargs["startaddr"],int) == False:
            raise TypeError("startaddr should be integer type")    
        addr=kwargs["startaddr"]
    
    if "enableaddr" in kwargs:
        if isinstance(kwargs["enableaddr"],bool) == False:
            raise TypeError("enableaddr should be boolean type ( True/False )")    
        enaddr = kwargs["enableaddr"]
    
    szret = ""
    
    for i in range(len(pdu)//lenblock):
        if(enaddr):
            szret = szret + "| %4.4X   " % addr
        else:
            szret = szret + "| "
        szret = szret + "".join("%2.2X " % c for c in pdu[i*lenblock : (i*lenblock) + lenblock])
        # ingat! ada karakter spasi di operasi join diatas
        szret = szret + "|" #"|\n"
        addr = addr + lenblock
     
    sisa=len(pdu) % lenblock
    if sisa == 0:
        return szret
    
    
    if(enaddr):
        szret = szret + "| %4.4X   " % addr
    else:
        szret = szret + "| "        
        
    szret = szret + "".join("%2.2X " % c for c in pdu[len(pdu)-sisa : len(pdu)])
    szret = szret + "".join(" . " for c in range(lenblock-sisa)) + "|" #"|\n"
    return szret

    
def readflash(con,bank,startaddr,len):
    if(endaddr > (0x21ffe+0x8000)):
        raise RuntimeError("Cann't read at address > 0x21ffe")
    
    # Select Bank
    select_bank(bank)
    
    datapoll=[]
    lendata = len
    addr = startaddr
    for idx in range(len//128) :
        msbaddr = (addr >> 8) & 0xff
        lsbaddr = addr & 0xff
        resp = con.transceive(bytearray([0x51,0x04,msbaddr,lsbaddr,128]))
        datapoll.extend(get_response_data(resp))
        addr = addr + 128
        lendata = lendata - 128
    
    msbaddr = (addr >> 8) & 0xff
    lsbaddr = addr & 0xff
    resp = con.transceive(bytearray([0x51,0x04,msbaddr,lsbaddr,lendata]))
    datapoll.extend(get_response_data(resp))
    return datapoll
            

# def dumptofile(szfname,*args,**keywords):
    # fname = open(CONFIG.LOGPATH+"//"+szfname,'a+')
    # fname.write("[ " + time.strftime("%d-%m-%Y %H:%M:%S")+ " scard-id: " + CONFIG.SCARD_ID +" ] ")
    # fname.write('\n')
    # for i in args:
        # fname.write('%s ' % i)
    # fname.write("\n")
    # if('apdu' in keywords):
        # szapdu = str()
        # szapdu = " ".join("%2.2X" % c for c in keywords["apdu"])
        # fname.write('    apdu     : %s\n' % szapdu)
        
    # if('address' in keywords):
        # fname.write('    address  : 0x%4.4x\n' % keywords['address'])
    # if('bank_number' in keywords):
        # fname.write('    bank     : %d\n' % keywords['bank_number'])
    # if('result' in keywords):
        # fname.write('    result   : %s\n' % keywords['result'])
    # if('expected' in keywords):
        # fname.write('    expected : %s\n' % keywords['expected'])
    # fname.write("\n")
    # fname.write("\n")
    # fname.flush()
    # fname.close()

    
# def dumptofilestats(szfname,*args,**keywords):
    # fname = open(CONFIG.LOGPATH+"//"+szfname,'a+')
    # fname.write("[ " + time.strftime("%d-%m-%Y %H:%M:%S")+ " scard-id: " + CONFIG.SCARD_ID +" ] ")
    # fname.write('\n')
    # for i in args:
        # fname.write('%s ' % i)
    # keys = sorted(keywords.keys())    
    # for kw in keys:
        # fname.write("\n")
        # fname.write("    ")
        # fname.write("{0:22s}: {1:s}".format(kw,str(keywords[kw])))
    # fname.write("\n\n\n")
    # fname.flush()
    # fname.close()

    
def readallcell(con,startaddr,endaddr,expected):
    for addr in range(endaddr , startaddr-1, -1):
        value = read_cell(con,addr)
        if(value != expected):
            raise ReadError("Error Validation",addr,value)

                    
