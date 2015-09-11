from bs4 import BeautifulSoup
import urllib.request
import urllib.error
import json

def questionsByCategory(cat, outputfilename):
    baseurl = 'http://answers.yahoo.com'
    cur_url = baseurl + cat

    # how many questions we want to get
    count = 10000
    while count > 0:
        print(count)
        html = urllib.request.urlopen(cur_url).readall()
        qids = get_question_ids(html)
        count -= len(qids)

        # if there were no questions on that page, cut it out.
        # if len(qids) == 0:
        #     return 'no more questions'

        # save returned question ids to the output file
        with open(outputfilename, 'a') as out:
            for qid in qids:
                out.write('%s\n' % qid)


        # parse questions here

        # determine where to go next for more questions

        parser = BeautifulSoup(html)
        print(cur_url)
        # there might not be more questions. In this case we return.
        correct_match = parser(text='Click me to see next set of Questions!')
        if len(correct_match) == 0:

            return 'no more pages'

        nexturl = parser(text='Click me to see next set of Questions!')[0].parent
        nexturl = nexturl['href']
        cur_url = baseurl + nexturl

    return 'done'


def get_question_ids(html):
    soup = BeautifulSoup(html)
    qids = []
    # find the right spot
    m = False
    ya = False

    for ul in soup('ul'):
        if ul.get('role') and ul['role'] == 'main':
            m = True
        if ul.get('id') and ul['id'] == 'ya-discover-tab':
            ya = True
        if m and ya:
            break

    # check if m and ya are True. Otherwise there're no questions on this page.
    if not (m and ya):
        return []

    # ul now is a tag that contains our questions
    children = ul.findChildren()
    for child in children:
        if child.name == 'li' and child.get('data-id'):
            qids.append(child['data-id'])
    return qids

def get_main_categories_ids(html):
    with open('data/categories_ids.txt', 'w') as cat_ids:


        soup = BeautifulSoup(html)
        divs = soup.findAll(lambda tag: tag.name == 'div' and tag.get('id') and tag['id'] == 'ya-cat-all')

        soup = BeautifulSoup(str(divs[0]))
        cats = [li.extract() for li in soup('li')]

        start_recording = False

        for c in cats:
            # if not c.children:
            #     continue

            for child in c.children:
                if child.name == 'a' and child.get('class') and 'selected' in child['class']:
                    start_recording = True

                if child.name == 'a' and child.get('class') and 'unselected' in child['class'] and start_recording:
                    # print(child['class'])
                    cat_ids.write('%s\n' % child['href'])
                    print('%s-%s' % (child['title'], child['href']))
                    # new_url = base_url+c['data-spaceid']
                    # new_html = urllib.request.urlopen(new_url).readall()
                    # get_categories_ids(new_html)

def get_subcategories_ids_from_file(filename):
    with open(filename) as input_file:
        for cat_id in input_file:
            get_subcategories_ids(cat_id.strip())

def get_subcategories_ids(cat):
    with open('data/subcategories.txt', 'a') as output:
        base_url = 'https://answers.yahoo.com'
        html = urllib.request.urlopen(base_url + cat).readall()
        soup = BeautifulSoup(html)

        divs = soup.find_all(lambda tag: tag.name == 'div' and tag.get('class') and 'Op-0-9' in tag['class'])
        div = divs[0]

        for child in div.children:
            if child.name == 'a' and child.get('href'):
                print('%s-%s' % (str(child.next), child['href']))
                output.write('%s\n' % child['href'])
                get_subcategories_ids(child['href'])

def get_question_answer_by_id(qid):

    # ok
    def get_questions_title(soup):
        for h1 in soup('h1'):
            if h1.get('class') and 'Fz-24' in h1['class'] and 'Fw-300' in h1['class'] and 'Mb-10' in h1['class']:
                # print(h1.text.strip())
                return h1.text.strip()

    def get_question_id(soup):
        return 1

    # ok
    def get_div_text(question_div):
        text = ''
        full_text = ''
        for child in question_div.children:
            if child.name == 'span' and child.get('class') and 'ya-q-text' in child['class']:
                text = child.text
            if child.name == 'span' and child.get('class') and 'ya-q-full-text' in child['class']:
                full_text = child.text
        result = full_text if full_text else text
        return result

    def get_answers(soup):
        answers = []
        for div in soup('div'):
            if div.get('class') and 'answer-detail' in div['class'] and 'Fw-n' in div['class']:
                for child in div.children:
                    if child.name == 'span' and child.get('class') and 'ya-q-full-text' in child['class']:
                        answers.append(child.text)

        return answers

    # not used
    def get_question_answers(soup):
        required_names = ['D-ib', 'Py-7', 'Px-10', 'Bdx-1g', 'Fw-13']
        for div in soup('div'):
            if div.get('class'):
                for n in required_names:
                    if n not in div['class']:
                        continue
                if div.text == 'next':
                    next = div.parent['href']



        # ok

    # ok
    def is_question_div(div):
        return div.get('class') and 'Fz-13' in div['class'] and 'Fw-n' in div['class'] and 'Mb-10' in div['class']

    # ok
    def get_question_text(soup):
        found_q = False
        question_div = ''
        update_div = []
        for div in soup('div'):
            if is_question_div(div):
                if not found_q:
                    found_q = True
                    question_div = div
                else:
                    update_div.append(div)

        question_text = get_div_text(question_div)
        for upd in update_div:
            question_text += ' ' + get_div_text(upd)
        return question_text


    base_url = 'https://answers.yahoo.com/question/index?qid='
    url = base_url + qid
    html = urllib.request.urlopen(url).readall()

    soup = BeautifulSoup(html)

    question_text = get_question_text(soup)
    title = get_questions_title(soup)
    answers = get_answers(soup)

    packed_q = json.dumps({'qid': qid, 'title': title, 'question': question_text, 'answers': answers})
    return packed_q




if __name__ == '__main__':

    with open('data/questions_nonexistent.txt', 'a') as output:
        with open('data/qids_nonexistent.txt') as qids:
            for qid in qids:
                qid = qid.strip()
                print('Processing qid: %s' % qid)
                try:
                    packed_q = get_question_answer_by_id(qid)
                    output.write('%s\n' % str(packed_q))
                except AttributeError:
                    print('Exception occured')
                    continue
                except urllib.error.HTTPError as e:
                    print(e.code)
                    if e.code == 500:
                        from time import sleep
                        sleep(120)
                        continue

    # with open('data/cats.txt') as cats:
    #     for cat in cats:
    # #         html = urllib.request.urlopen('https://answers.yahoo.com' + cat.strip()).readall()
    #
    #         status = questionsByCategory(cat, 'data/qids.txt')
    #         print(status)
    # html = urllib.request.urlopen('https://answers.yahoo.com/dir/index').readall()
    # get_main_categories_ids(html)

    # get_subcategories_ids_from_file('data/categories_ids.txt')



def list_of_categories_ids():
    # categories ids
    #1. art_and_humanities = 396545012
    books_and_authors = 396545299
    history = 396545298
    philisophy = 396545231
    # visual arts
    drawing_and_illustration = 396546035
    photography = 396546037
    other_visual_arts = 396546039
    sculpture = 396546038
    painting = 396546036

    dancing = 396545374
    other_arts_and_humanities = 396545310
    poetry = 2115500137
    genealogy = 396546034
    performing_arts = 396545300
    theatre_and_acting = 396546419

    # 2. beauty_and_style = 396545144
    fashion_and_accessories = 396545392
    hair = 396546058
    makeup = 396546059
    other_beauty_and_style = 396546061
    other_skin_and_body = 396547157
    tattoos = 396547156

    # 3. computers_and_internet = 396545660
    computer_networking = 396545676
    #hardware
    addons = 396545669
    monitors = 396545672
    scanners = 396545674
    desktops = 396545670
    other_hardware = 396545675
    laptops_and_notebooks = 396545671
    printers = 396545673

    programming_and_design = 396545663
    #internet
    facebook = 2115500145
    msn = 2115500144
    wikipedia = 2115500146
    flickr = 2115500147
    myspace = 2115500140
    youtube = 2115500142
    google = 2115500141
    other_internet = 2115500139

    security = 396546062

    # 4. health = 396545018
    alternative_medicine = 396545175
    #deseases and conditions
    allergies = 396545383
    heart_deseases = 396545385
    respiratory_deseases = 396545388
    cancer = 396545116
    infectious_deseases = 396545386
    STDs = 396545390
    diabetes = 396545384
    other_deseases = 396545391
    skin_conditions = 396545389

    mental_health = 396546043
    womens_health = 396545203
    dental = 396545381
    #general health care 396545143
    first_aid = 396546498
    pain_and_pain_management = 396547122
    injuries = 396546499
    other_general_health_care = 396546500

    optical = 2115500199
    diet_and_fitness = 396545382
    mens_health = 396545224
    other_health = 396545393

    # 5.home_and_garden 396545394
    cleaning_and_laundry = 396545395
    garden_and_landscape = 396545397
    decorating_and_remodelling = 396545396
    maintenance_and_repair = 396545398
    do_it_yourself = 396546406
    other_home_and_garden = 396545400

    # 6.pets = 396545443
    birds = 396546023
    fish = 396546024
    repltiles = 396546022
    cats = 396546020
    horses = 2115500432
    rodents = 2115500150
    dogs = 396546021
    other_pets = 396546025

    # 7. sports = 396545213
    #autoracing 396545601
    formula_one = 396547186
    indy_racing_league = 396547188
    nascar = 396547187
    other_autoracing = 396547189

    baseball = 396545232
    basketball = 396545233
    boxing = 396546410
    cricket = 396545459
    cycling = 396545460
    fantasy_sports = 396545236
    football_american = 396545234
    #footbal_australian = 396546111
    australian_rules = 396546517
    other_football = 396546518
    rugby_league = 396546515
    rugby_union = 396546516

    football_canadian = 396546112
    #football_soccer = 396545464
    # !todo

    golf = 396545461
    handball = 396546520
    hockey = 396545462
    horse_racing = 396546113
    martial_arts = 396546519
    motorcycle_racing = 2115500156
    olympics = 396546114
    other_sports = 396545468
    #outdoor_recreation = 396545186
    camping = 2115500157
    hunting = 396546413
    climbing = 2115500158
    other_outdoor_recreation = 396546415
    fishing = 396546414

    rugby = 396545463
    running = 396547165
    snooker_and_pool = 396546115
    surfing = 2115500159
    swimming_and_diving = 396545465
    tennis = 396545235
    volleyball = 396545466
    water_sports = 396546085
    #winter_sports = 396545467
    curling = 396546109
    ice_skating = 396547176
    other_winter_sports = 396547178
    snow_skiing = 396547175
    snowboarding = 396547177

    wrestling = 396546411

    # 8. travel = 396545469
    #africa_and_middle_east = 396545470
    algeria = 2115500177
    bahrain = 396545471
    egypt = 396545472
    israel = 396545473
    kenia = 396545474
    lebanon = 396545475
    madagascar = 396545476
    mauritius = 396545477
    morocco = 396545478
    other_africa_and_middle_east = 396545600
    saudi_arabia = 396545479
    seychelles = 396545480
    south_africa = 396545481
    tunisia = 396545482
    united_arab_emirates = 396545483

    air_travel = 396546521
    #argentina = 396545540
    bariloche = 396546888
    buenos_aires = 396546875
    carilo = 396546880
    cordoba = 396546885
    gualeguaychu = 396546889
    iguazu = 396546890
    la_plata = 396546877
    mar_de_plata = 396546878
    mendoza = 396546886
    miramar = 396546883
    other_argentina = 396546891
    pinamar = 396546879
    rosario = 396546884
    salta = 396546887
    san_bernardo = 396546882
    villa_gesell = 396546881

    #asia_pacific = 396545484
    china = 396545486
    indonesia = 396547129
    japan = 396545488
    korea = 396545489
    malaysia = 396545490
    maldives = 396545491
    other_asia_pacific = 396545498
    philippines = 396545493
    singapore = 396545494
    taiwan = 396545495
    thailand = 396545496
    #australia = 396545485
    adelaide = 396546145
    brisbane = 396546147
    canberra = 396546148
    darwin = 396546150
    hobart = 396546152
    melbourne = 396546153
    other_australia = 396546158
    perth = 396546154
    sydney = 396546156

    #austria = 396545523
    graz = 396546895
    linz = 396546894
    other_austria = 396546896
    salzburg = 396546893
    vienna = 396546892
    # todo. Finish these categories. They are freaking endless!





