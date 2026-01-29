import random
year = 2026
#DİKKAT:SKO(Reborn) İle Oluşturulan İçerikler Tamamen Örnek Veridir,Gerçek Kişiler Ve Kurumlar İle İlgisi Yoktur Ve Kötüye Kullanım Kullanıcının Sorumluluğundadır. https://pynet.neocities.org
#cinsiyete göre isim seçme
def namegen(cinsiyet):
    erkek_isim = ["Liam", "Noah", "Oliver", "Elijah", "James", "William", "Benjamin", "Lucas", "Henry", "Theodore", "Alexander", "Ethan", "Mason", "Michael", "Daniel", "Jacob", "Logan", "Jackson", "Sebastian", "Jack", "David", "Matthew", "Owen", "Samuel", "Joseph", "John", "Wyatt", "Gabriel", "Julian", "Anthony", "Levi", "Christopher", "Andrew", "Joshua", "Dylan", "Isaac", "Leo", "Lincoln", "Caleb", "Ryan"]
    kiz_isim = ["Olivia", "Emma", "Charlotte", "Amelia", "Sophia", "Isabella", "Ava", "Mia", "Evelyn", "Luna", "Harper", "Camila", "Sofia", "Scarlett", "Elizabeth", "Eleanor", "Chloe", "Violet", "Penelope", "Grace", "Lily", "Aria", "Ella", "Aurora", "Hannah", "Stella", "Hazel", "Zoe", "Victoria", "Nora", "Layla", "Brooklyn", "Everly", "Paisley", "Eliana", "Lucy", "Elena", "Leah", "Audrey", "Willow"]
    if cinsiyet == "erkek":
        isim = random.choice(erkek_isim)
        return isim
    elif cinsiyet == "kiz":
        isim = random.choice(kiz_isim)
        return isim
    else:
        return "bilinmeyen giriş"
#soyisim seçme
def surnamegen():
    soyadlar = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell", "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Reed", "Cook", "Morgan", "Cooper", "Diaz", "Morris"]
    surname = random.choice(soyadlar)
    return surname
#cinsiyett seçme
def gender_gen():
    gender = random.choice(["erkek","kiz"])
    return gender
#yaş seçme
def age_gen():
    age = random.randint(0,100)
    if age > 50:
        kisirlik = True
        k_reason = "Kısır (Yaşlılık)"
    elif age < 16:
        kisirlik = True
        k_reason = "Kısır (Reşit Değil)"
    else:
        kisirlik = random.choices([True,False],weights=[10,90],k=1)[0]
        if kisirlik == True:
         k_reason = "Kısır"
        else:
         k_reason = ""

    return age,kisirlik,k_reason
#din seçme
def rel_gen(age):
    dinler = ["İslam","Hristiyanlık","Budizim","Ateizim","Agnostizm","Yahudilik","Deizim"]
    if age > 4:
        din = random.choices(dinler,weights=[25,30,6,12,5,0.2,1.8],k=1)[0]
        return din
    else:
        return "Ateizim (Çocuk)"
#bağımlılıklar
#yapay zeka yardımı alındı-bug kaynaklı
def addict_gen(age, din):
    if age < 19:
        return "Bağımlı Değil(Çocuk)"
    
    addictions = ["Sigara Bağımlılığı Var", "Alkol Bağımlılığı Var", "Uyuşturucu Bağımlılığı Var"]
    
    if din in ["Ateizim", "Deizim", "Agnostizm"]:
        addicted = random.choices([True, False], weights=[30, 70], k=1)[0]
    else:
        addicted = random.choices([True, False], weights=[10, 90], k=1)[0]
    
    if addicted:
        return random.choice(addictions)
    else:
        return "Bağımlı Değil."
#ssn oluşturucu
def ssn_gen():
    ssn1 = ""
    ssn2 = ""
    ssn3 = ""
    a = 0
    b = 0
    c = 0
    runtime1 = 3
    runtime2 = 2
    runtime3= 4
    while a < 3:
        ssn1 = ssn1 + str(random.randint(0,9))
        a += 1
    while b < 2:
        ssn2 = ssn2 + str(random.randint(0,9))
        b += 1
    while c < 3:
        ssn3 = ssn3 + str(random.randint(0,9))
        c += 1
    return f"{ssn1}-{ssn2}-{ssn3}"
#cinsel yönelim oluşturucu
def sex_gen(gender,din):
    if gender == "erkek":
        sex = (random.choices(["Gay","Heteroseksüel","Trans","Non-Sexual"],weights=[5,90,2,3],k=1)[0])
        return sex
    elif gender == "kiz":
        sex = (random.choices(["Lezbiyen","Heteroseksüel","Trans","Non-Sexual"],weights=[5,90,2,3],k=1)[0])
        return sex
#doğum yeri oluşturucu
def state_gen():
    eyaletler = ["Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming"]
    state = random.choice(eyaletler)
    return state
#doğum tarihi oluşturucu
def born_date_gen(age):
    aylar = ["Ocak","Şubat","Mart","Nisan","Mayıs","Haziran","Temmuz","Ağustos","Eylül","Ekim","Kasım","Aralık"]
    b_year = year - age
    b_month = random.choice(aylar)
    b_day = ""
    if b_month != "Şubat":
        b_day = random.randint(1,28)
    else:
        b_day = random.randint(1,30)
    return f"{b_day} {b_month} {b_year}"
#evlilik
def legal_status(age):
    if age >= 18:
        marriage = (random.choices([True,False],weights=[65,35],k=1)[0])
        return marriage
#çocuk olma olasılığı
def kid_born(age,kisirlik,marriage):
    if kisirlik == False and age < 40 and marriage == True:
        kid = random.choices([True,False],weights=[70,30],k=1)[0]
    elif kisirlik == False and age > 40 and marriage == True:
        kid = random.choices([True,False],weights=[40,60],k=1)[0]
    elif kisirlik == False and age < 40 and marriage == False:
        kid = random.choices([True,False],weights=[10,90],k=1)[0]
    else:
        kid = random.choices([True,False],weights=[5,95],k=1)[0]
    if kid:
        kid_num = random.choices([1,2,3,4,5],weights=[50,30,10,5,5],k=1)[0]
        return kid_num
    else:
        return 0
def test():
    a = gender_gen()
    b = 25
    c = surnamegen()
    d = namegen(a)
    e = rel_gen(b)
    f = addict_gen(b,e)
    g = ssn_gen()
    h = sex_gen(a,e)
    i = state_gen()
    j = born_date_gen(b)
    ab = legal_status(b)
    abc = kid_born(b,False,ab)
    print("it works!")
    #ana fonksyon
def main():
    cinsiyet = gender_gen()
    name = namegen(cinsiyet)
    surname = surnamegen()
    age,kisirlik,k_reason = age_gen()
    din = rel_gen(age)
    bagimlilik = addict_gen(age,din)
    ssn = ssn_gen()
    sex = sex_gen(cinsiyet,din)
    eyalet = state_gen()
    born_date = born_date_gen(age)
    marriage = legal_status(age)
    kidnum = kid_born(age,kisirlik,marriage)
    print(f"{name} {surname},{age} Yaşında,{k_reason},{eyalet} Eyaletinde {born_date} Tarihinde Doğdu, Kendisi {din} Dinine Mensup,{bagimlilik},SSN'i {ssn},Kendisi {sex} {kidnum} Adet Çocuğu Var")