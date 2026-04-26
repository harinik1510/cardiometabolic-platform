import sqlite3
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

DOCTORS = [
    # Avadi
    ("Dr. I Syed Tariq", "syed.tariq@example.com", "600054", "Diabetologist", 15, 500, "9876543210"),
    ("Dr. K Prem Kumar", "prem.kumar@example.com", "600054", "Diabetologist", 20, 600, "9876543211"),
    ("Dr. K Sidharthan", "sidharthan@example.com", "600054", "Cardiologist", 25, 800, "9876543212"),
    
    # Kodambakkam
    ("Dr. Jyotirmaya Dash", "jyotirmaya.dash@example.com", "600024", "Cardiologist", 27, 1000, "9876543213"),
    ("Dr. S. Nagendra Boopathy", "boopathy@example.com", "600024", "Cardiologist", 22, 900, "9876543214"),
    ("Dr. K. Jaishankar", "jaishankar@example.com", "600024", "Cardiologist", 27, 1000, "9876543215"),
    ("Dr. R.P. Rajesh", "rp.rajesh@example.com", "600024", "Diabetologist", 20, 700, "9876543216"),
    ("Dr. Shivaa Mohan", "shivaa.mohan@example.com", "600024", "Diabetologist", 18, 650, "9876543217"),
    ("Dr. V. Mahadevan", "v.mahadevan@example.com", "600024", "Diabetologist", 18, 700, "9876543218"),
    
    # Madhavaram
    ("Dr. Ravindran T", "ravindran.t@example.com", "600060", "Cardio-Diabetic", 31, 850, "9876543219"),
    ("Dr. Priya Jaiganesh", "priya.jaiganesh@example.com", "600060", "Diabetologist", 19, 600, "9876543220"),
    ("Dr. Deeyaneswar D", "deeyaneswar@example.com", "600060", "Cardiologist", 11, 750, "9876543221"),
    ("Dr. Harikrishnan Parthasarathy", "harikrishnan.p@example.com", "600060", "Cardiologist", 30, 950, "9876543222"),
    
    # Tambaram
    ("Dr. Stalin Roy J", "stalin.roy@example.com", "600045", "Cardiologist", 20, 800, "9876543223"),
    ("Dr. Narendra Kumar V", "narendra.kumar@example.com", "600045", "Cardiologist", 25, 900, "9876543224"),
    ("Dr. Ganesh V", "ganesh.v@example.com", "600045", "Cardiologist", 28, 850, "9876543225"),
    ("Dr. M. Nandakumaran", "nandakumaran@example.com", "600045", "Cardiologist", 33, 1000, "9876543226"),
    ("Dr. Ashwin Karuppan", "ashwin.karuppan@example.com", "600045", "Diabetologist", 18, 700, "9876543227"),
    ("Dr. Selvakumar J", "selvakumar.j@example.com", "600045", "Diabetologist", 25, 750, "9876543228"),
    ("Dr. Prasanna Kumar Gupta P", "prasanna.gupta@example.com", "600045", "Diabetologist", 30, 800, "9876543229"),
    ("Dr. Aafrin Shabbir", "aafrin.shabbir@example.com", "600045", "Diabetologist", 15, 650, "9876543230"),
    ("Dr. N. N. Anand", "nn.anand@example.com", "600045", "Diabetologist", 26, 700, "9876543231"),
    
    # Anna Nagar
    ("Dr. Sandhya S", "sandhya.s@example.com", "600040", "Cardiologist", 17, 850, "9876543232"),
    ("Dr. E. Satish Kumar", "satish.kumar@example.com", "600040", "Cardiologist", 20, 1000, "9876543233"),
    ("Dr. Deepesh Venkatraman", "deepesh.v@example.com", "600040", "Cardiologist", 20, 900, "9876543234"),
    ("Dr. Vasanth Kumar", "vasanth.kumar@example.com", "600040", "Diabetologist", 25, 800, "9876543235"),
    ("Dr. Ramkumar S", "ramkumar.s@example.com", "600040", "Diabetologist", 20, 750, "9876543236"),
    
    # Pallavaram
    ("Dr. G.V. Senthilnathan", "senthilnathan@example.com", "600043", "Cardiologist", 25, 950, "9876543237"),
    ("Dr. S. Ramesh", "s.ramesh@example.com", "600043", "Cardiologist", 28, 900, "9876543238"),
    ("Dr. Jagan Gajarajan", "jagan.g@example.com", "600043", "Cardiologist", 22, 850, "9876543239"),
    ("Dr. Asha Moorthy", "asha.moorthy@example.com", "600043", "Cardiologist", 20, 800, "9876543240"),
    ("Dr. Deep Chandh Raja S", "deep.chandh@example.com", "600043", "Cardiologist", 15, 1100, "9876543241"),
    ("Dr. Rohith", "rohith@example.com", "600043", "Diabetologist", 11, 550, "9876543242"),
    ("Dr. Ranjith Pratap S", "ranjith.pratap@example.com", "600043", "Diabetologist", 18, 700, "9876543243"),
    ("Dr. Suresh Kanna S", "suresh.kanna@example.com", "600043", "Diabetologist", 10, 600, "9876543244"),
    ("Dr. Dharmarajan Panneerselvam", "dharmarajan.p@example.com", "600043", "Diabetologist", 33, 900, "9876543245"),
    
    # Egmore
    ("Dr. C.T. Anand Moses", "anand.moses@example.com", "600008", "Cardiologist", 26, 950, "9876543246"),
    ("Dr. Roy Santosham J.D.", "roy.santosham@example.com", "600008", "Cardiologist", 39, 1200, "9876543247"),
    ("Dr. R. Hariharakrishnan", "hariharakrishnan@example.com", "600008", "Cardiologist", 22, 850, "9876543248"),
    ("Dr. Prakash Chand Jain", "prakash.jain@example.com", "600008", "Cardiologist", 25, 1000, "9876543249"),
    ("Dr. Nagarajan Solai", "nagarajan.solai@example.com", "600008", "Cardiologist", 25, 900, "9876543250"),
    ("Dr. A. Ramachandran", "ramachandran@example.com", "600008", "Diabetologist", 35, 1100, "9876543251"),
    ("Dr. D. Shantharam", "shantharam@example.com", "600008", "Diabetologist", 35, 1000, "9876543252"),
    ("Dr. Mohan V.", "mohan.v@example.com", "600008", "Diabetologist", 40, 1500, "9876543253"),
    ("Dr. Anbazhahan Rajaram", "anbazhahan.r@example.com", "600008", "Diabetologist", 35, 900, "9876543254"),
    ("Dr. D.K. Sriram", "dk.sriram@example.com", "600008", "Diabetologist", 30, 950, "9876543255"),
]

def seed_doctors():
    conn = sqlite3.connect('data/platform.db')
    cursor = conn.cursor()
    
    password = hash_password('doctor123') # Default password for all doctors for now
    
    for doc in DOCTORS:
        name, email, pincode, spec, exp, fees, phone = doc
        try:
            cursor.execute('''
            INSERT INTO users (name, email, password, role, pincode, specialization, experience, fees, phone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, email, password, 'doctor', pincode, spec, exp, fees, phone))
        except sqlite3.IntegrityError:
            print(f"Doctor {email} already exists.")
            
    conn.commit()
    conn.close()

if __name__ == '__main__':
    seed_doctors()
    print("Doctors seeded successfully.")
