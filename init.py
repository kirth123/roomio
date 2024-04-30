from flask import Flask, render_template, request, session, redirect
import pymysql.cursors
import bcrypt
import app
from flask import Flask
import datetime

conn = pymysql.connect(host='localhost',
                       port = 3306,
                       user='root',
                       password='root',
                       db='apartments',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)
app = Flask(__name__)

@app.route('/register', methods=['GET'])
def register():
    return render_template('register.html')

@app.route('/registerAuth', methods=['POST'])
def registerAuth():
    username = request.form['username']
    firstname = request.form['firstname']
    lastname = request.form['lastname']
    DOB = request.form['DOB']
    gender = 1 if request.form['gender'] == 'male' else 2 #male = 1, female = 2
    email = request.form['email']
    phone = request.form['phone']
    passwd = str.encode(request.form['passwd'])
    salt = bcrypt.gensalt()
    hash = bcrypt.hashpw(passwd, salt)

    cursor = conn.cursor()
    query = 'SELECT * from users WHERE username = %s'
    cursor.execute(query, (username))
    data = cursor.fetchone()

    if(data):
        error = "This user already exists"
        return render_template('register.html', error = error)
    else:
        ins = 'INSERT INTO users (username, first_name, last_name, DOB, gender, email, Phone, passwd) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)'
        cursor.execute(ins, (username, firstname, lastname, DOB, gender, email, phone, hash))
        conn.commit()
        cursor.close()
        return render_template('login.html')

@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')

@app.route('/loginAuth', methods=['POST'])
def loginAuth():
    if not request.form['username'] or not request.form['passwd']:
        error = "You didn't give a username or password"
        return render_template('login.html', error = error)

    username = request.form['username']
    passwd = str.encode(request.form['passwd'])

    cursor = conn.cursor()
    query = 'SELECT passwd FROM users WHERE username = %s'
    cursor.execute(query, (username))
    data = cursor.fetchone()

    if (data):
        if bcrypt.checkpw(passwd, str.encode(data['passwd'])):
            session['username'] = username
            msg = f"You're logged in now, {session['username']}" 
            return render_template('login.html', error = msg)
        else:
            return render_template('login.html')
    else:
        error = "Incorrect username or password"
        return render_template('login.html', error = error)

@app.route('/logout', methods=['GET'])
def logout():
    session.pop('username')
    return render_template('login.html')

@app.route('/searchInterest', methods=['GET'])
def searchInterest():
    return render_template('searchinterest.html')

@app.route('/searchInterestAuth', methods=['GET', 'POST'])
def searchInterestAuth():
    if not session.get('username'):
        return redirect('/login')

    roommatecnt = request.args.get('roommatecnt')
    if request.args.get('moveindate'):
        moveindate = datetime.datetime.strptime(request.args.get('moveindate'), '%Y-%m-%d').date()
    else:
        moveindate = None
    error = "No one has expressed an interest in the apartments that you want"
    cursor = conn.cursor()

    if roommatecnt and moveindate:
        query = 'SELECT * FROM interests WHERE RoommateCnt = %s AND MoveInDate = %s'
        cursor.execute(query, (roommatecnt, moveindate))
        apts = cursor.fetchall()
    elif roommatecnt:
        query = 'SELECT * FROM interests WHERE RoommateCnt = %s'
        cursor.execute(query, (roommatecnt))
        apts = cursor.fetchall()
    else:
        query = 'SELECT * FROM interests WHERE MoveInDate = %s'
        cursor.execute(query, (moveindate))
        apts = cursor.fetchall()

    if apts:
        return render_template('searchinterest.html', apts = apts)
    else:
        return render_template('searchinterest.html', error = error)

@app.route('/postInterest', methods=['GET'])
def postInterest():
    return render_template('postinterest.html')

@app.route('/postInterestAuth', methods=['POST'])
def postInterestAuth():
    if not session.get('username'):
        return redirect('/login')

    username = session['username']
    unitrentid = request.form['unitrentid']
    roommatecnt = request.form['roommatecnt']
    moveindate = datetime.datetime.strptime(request.form['moveindate'], '%Y-%m-%d').date()

    cursor = conn.cursor()
    query = 'SELECT UnitRentID FROM interests WHERE UnitRentID = %s'
    cursor.execute(query,  (unitrentid))
    data = cursor.fetchone()

    if not data:
        query = 'SELECT AvailableDateForMoveIn FROM apartmentunit WHERE UnitRentID = %s'
        cursor.execute(query, (unitrentid))
        tmp = cursor.fetchone()
        if tmp and moveindate != tmp['AvailableDateForMoveIn']:
            error = f"The apartment is not available by this date. It's available by {tmp['AvailableDateForMoveIn']}."
            return render_template('postinterest.html', error = error)

        cursor = conn.cursor()
        ins = 'INSERT INTO interests (username, UnitRentID, RoommateCnt, MoveInDate) VALUES(%s, %s, %s, %s)'
        cursor.execute(ins, (username, unitrentid, roommatecnt, moveindate))
        cursor.fetchone()
        error = "Your interest has been registered."
        return render_template('postinterest.html', error = error)
    else:
        print(data)
        error = "Someone has already expressed interest in this unit. You can choose to join their group instead."
        return render_template('postinterest.html', error = error)

@app.route('/viewInterest', methods=['GET'])
def viewInterest():
    if not session.get('username'):
        return redirect('/login')
    if not request.args.get('unit'):
        return render_template('viewinterest.html', error = "Please provide a unit that you want to view interests for")

    unit = request.args.get('unit')
    cursor = conn.cursor()
    query = 'SELECT * FROM interests WHERE UnitRentID = %s'
    cursor.execute(query, (unit))
    ppl = cursor.fetchall()
    return render_template('viewinterest.html', ppl = ppl)

@app.route('/initiator', methods=['GET'])
def initiateAuth():
        if not session.get('username'):
            return redirect('/login')

        contact = request.args.get('contact')
        if contact:
            cursor = conn.cursor()
            query = 'SELECT username, DOB, gender, first_name, last_name, email, Phone FROM users WHERE username = %s'
            cursor.execute(query, (contact))
            data = cursor.fetchone()

            if not data:
                error = "This user doesn't exist."
                return render_template('initiator.html', error = error)
            else:
                if data['gender'] == 2:
                    data['gender'] = 'Female'
                else:
                    data['gender'] = 'Male'
                return render_template('initiator.html', data = data)   
        else:
            error = "You need to provide a username to reference."
            return render_template('initiator.html', error = error)   

@app.route('/searchApt', methods=['GET'])
def search():
    return render_template('searchapt.html')    

@app.route('/searchAptAuth', methods=['POST'])
def searchAuth():
    if not session.get('username'):
        return redirect('/login')

    bldg = request.form['bldg']
    comp = request.form['company']
    user = session['username']

    cursor = conn.cursor()  
    query = 'SELECT pets.PetName, pets.PetSize, pets.PetType, pp.isAllowed, pp.MonthlyFee, pp.RegistrationFee FROM petpolicy pp NATURAL JOIN pets WHERE pets.username = %s AND pp.BuildingName = %s AND pp.CompanyName = %s'
    cursor.execute(query, (user, bldg, comp))
    items = cursor.fetchall()
    print(items)

    for item in items:
        item['isAllowed'] = 'Yes' if item['isAllowed'] else 'No'

    query = 'SELECT unit.* FROM apartmentunit unit WHERE unit.BuildingName = %s AND unit.CompanyName = %s'
    cursor.execute(query, (bldg, comp))
    apts = cursor.fetchall()
    tmp = []
    visited = set()

    for i in range(len(apts)):
        if apts[i]['UnitRentID'] not in visited:
            query = 'SELECT COUNT(rooms.name) as cnt FROM apartmentunit unit JOIN rooms on unit.UnitRentID = rooms.UnitRentID WHERE unit.UnitRentID = %s'
            cursor.execute(query, (apts[i]['UnitRentID']))
            var = cursor.fetchone()
            tmp.append(apts[i])
            tmp[i]['cnt'] = var['cnt']
            visited.add(tmp[i]['UnitRentID'])

    return render_template('searchapt.html', apts = tmp, pets = items)

@app.route('/registerPets', methods=['GET'])
def registerPets():
    return render_template('registerpets.html')

@app.route('/registerPetsAuth', methods=['POST'])
def registerPetsAuth():
    if not session.get('username'):
        return redirect('/login')

    petname = request.form['petname']
    pettype = request.form['pettype']
    petsize = request.form['petsize']
    cursor = conn.cursor()

    query = 'SELECT * FROM pets where petname = %s AND pettype = %s AND petsize = %s AND username = %s'
    res = cursor.execute(query, (petname, pettype, petsize, session['username']))
    if not res: 
        ins = 'INSERT INTO pets (petname, pettype, petsize, username) VALUES(%s, %s, %s, %s)'
        cursor.execute(ins, (petname, pettype, petsize, session['username']))
        msg = 'You have registered this pet successfully'
        return render_template('registerpets.html', error = msg)
    else:
        error = "You've already registered this pet"
        return render_template('registerpets.html', error = error)

@app.route('/editPets', methods=['GET'])
def editPets():
    return render_template('editpets.html')

@app.route('/editPetsAuth', methods=['POST'])
def editPetsAuth():
    if not session.get('username'):
        return redirect('/login')

    oldpetname = request.form['oldpetname']
    oldpettype = request.form['oldpettype']
    newpetname = request.form['newpetname']
    newpettype = request.form['newpettype']
    newpetsize = request.form['newpetsize']
    user = session['username']
    cursor = conn.cursor()

    query = 'SELECT * FROM pets where PetName = %s AND PetType = %s AND username = %s'
    cursor.execute(query, (oldpetname, oldpettype, user))
    res = cursor.fetchone()

    if not res: 
        error = "You've not registered a pet with this name or type."
        return render_template('editpets.html', error = error)
    else:
        query = 'SELECT * FROM pets where PetName = %s AND PetType = %s AND username = %s'
        cursor.execute(query, (newpetname, newpettype, user))
        res = cursor.fetchall()

        if not res:
            ins = 'UPDATE IGNORE pets SET PetName = %s, PetType = %s, PetSize = %s WHERE username = %s'
            cursor.execute(ins, (newpetname, newpettype, newpetsize, user))
            msg = "You have updated your pet's information successfully."
            return render_template('editpets.html', error = msg)
        else:
            error = "You already have a pet with this name and type."
            return render_template('editpets.html', error = error)

@app.route('/estimateRent', methods=['GET'])
def estimateRent():
    return render_template('estimaterent.html')

@app.route('/estimateRentAuth', methods=['GET', 'POST'])
def estimateRentAuth():
    if not session.get('username'):
        return redirect('/login')

    zipcode = request.form['zipcode']
    numrooms = request.form['xbxb']

    cursor = conn.cursor() 
    query = 'SELECT unit.MonthlyRent as rent FROM apartmentbuilding bldg NATURAL JOIN apartmentunit unit JOIN rooms on unit.UnitRentID = rooms.UnitRentID WHERE bldg.AddrZipCode = %s GROUP BY unit.UnitRentID HAVING COUNT(rooms.name) = %s'
    cursor.execute(query, (zipcode, numrooms)) 
    rents = cursor.fetchall()
    total = 0
    i = 0

    for rent in rents:
        total += rent['rent']
        i += 1 

    if total > 0:
        avg = '{0:.{1}f}'.format(total / i, 2)
        return render_template('estimaterent.html', rent = avg)
    else:
        error = 'Failed to find apartments that match your specifications'
        return render_template('estimaterent.html', error = error)
    
@app.route('/display', methods=['GET'])
def display():
    return render_template('display.html')

@app.route('/displayAuth', methods=['GET', 'POST'])
def displayAuth():
    if not session.get('username'):
        return redirect('/login')

    search = request.form['search']
    cursor = conn.cursor()
    query = 'SELECT * FROM apartmentbuilding WHERE BuildingName = %s'
    cursor.execute(query, (search))
    res = cursor.fetchone()

    if res:
        yr = res['YearBuilt']
        addr = f"{res['AddrNum']} {res['AddrStreet']} \n {res['AddrCity']}, {res['AddrState']}, {res['AddrZipCode']}"
        cursor = conn.cursor()
        query = 'SELECT COUNT(unit.UnitRentID) as cnt, aType FROM apartmentunit unit NATURAL JOIN provides WHERE unit.BuildingName = %s GROUP BY unit.BuildingName'
        cursor.execute(query, (search))
        res = cursor.fetchall()

        if res:
            tmp = [item['aType'] for item in res]
            cnt = res[0]['cnt']
            return render_template('display.html', data = {'type': 'building', 'yr': yr, 'addr': addr, 'aType': ', '.join(tmp), 'cnt': cnt})
        else:
            return render_template('display.html', data = {'type': 'building', 'yr': yr, 'aType': '', 'cnt': cnt})
    else:
        cursor = conn.cursor()
        query = 'SELECT * FROM apartmentunit WHERE UnitRentID = %s'
        cursor.execute(query, (search))
        res = cursor.fetchone()

        if res:
            rent = res['MonthlyRent']
            date = res['AvailableDateForMoveIn']
            sq = res['squareFootage']
            cursor = conn.cursor()
            query = 'SELECT COUNT(rooms.name) as cnt FROM apartmentunit unit JOIN rooms on unit.UnitRentID = rooms.UnitRentID WHERE unit.UnitRentID = %s GROUP BY unit.UnitRentID'
            cursor.execute(query, (search))
            res = cursor.fetchone()

            if res:
                return render_template('display.html', data = {'type': 'unit', 'sq': sq, 'rent': rent, 'cnt': res['cnt'], 'date': date})
            else:
                return render_template('display.html', data = {'type': 'unit', 'sq': sq, 'rent': rent, 'cnt': 0, 'date': date})
        else:
            error = "We couldn't find any unit or building that matched the information given."
            return render_template('display.html', error = error)

app.secret_key = ";wm0Mv0B8~Aj"
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)