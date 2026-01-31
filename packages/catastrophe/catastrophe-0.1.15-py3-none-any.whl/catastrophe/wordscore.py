from __future__ import annotations

import math
import re
from collections import Counter
from typing import Dict, Iterable

# ============================================================
# CONFIG
# ============================================================

WORD_WEIGHT = 1.0
FREQ_WEIGHT = 0.4
PENALTY_WEIGHT = 0.6

WORD_RE = re.compile(r"[a-zA-ZÀ-ÿ']+")

# ============================================================
# LANGUAGE WORD LISTS (>=300 words each)
# ============================================================

LANG_WORDS: Dict[str, set[str]] = {}

# ---------------- ENGLISH ----------------
LANG_WORDS["en"] = {
    "the","be","to","of","and","a","in","that","have","i","it","for","not","on","with",
    "he","as","you","do","at","this","but","his","by","from","they","we","say","her",
    "she","or","an","will","my","one","all","would","there","their","is","are","was",
    "were","been","being","can","could","should","shall","may","might","must","if",
    "then","else","when","while","where","why","how","what","who","whom","which",
    "because","about","into","through","over","after","before","between","without",
    "under","again","further","once","here","there","both","each","few","more","most",
    "other","some","such","only","own","same","so","than","too","very",
    "man","woman","child","people","time","year","day","week","month","life","world",
    "school","state","family","student","group","country","problem","hand","part",
    "place","case","point","government","company","number","system","work","program",
    "question","fact","home","water","room","mother","father","area","money","story",
    "issue","side","kind","head","house","service","friend","power","hour","game",
    "line","end","member","law","car","city","community","name","president","team",
    "minute","idea","kid","body","information","back","parent","face","others",
    "level","office","door","health","person","art","war","history","party","result",
    "change","morning","reason","research","girl","guy","moment","air","teacher",
    "force","education","foot","boy","age","policy","process","music","market",
    "sense","nation","plan","college","interest","death","experience","effect",
    "use","useful","used","using","make","made","making","take","taken","taking",
    "give","given","giving","get","got","getting","see","seen","seeing","go","went",
    "going","come","came","coming","think","thought","thinking","know","knew",
    "knowing","look","looked","looking","want","wanted","wanting","find","found",
    "finding","tell","told","telling","ask","asked","asking","work","worked",
    "working","try","tried","trying","leave","left","leaving","call","called",
    "calling","feel","felt","feeling","become","became","becoming","show","shown",
    "showing","hear","heard","hearing","play","played","playing","run","ran",
    "running","move","moved","moving","live","lived","living","believe","believed",
    "believing","bring","brought","bringing","happen","happened","happening",
    "write","written","writing","provide","provided","providing","sit","sat",
    "sitting","stand","stood","standing","lose","lost","losing","pay","paid","paying",
    "meet","met","meeting","include","included","including","continue","continued",
    "continuing","set","sets","setting","learn","learned","learning","change",
    "changed","changing"
}

# ---------------- ITALIAN ----------------
LANG_WORDS["it"] = {
    "il","lo","la","i","gli","le","un","uno","una","di","a","da","in","con","su","per",
    "tra","fra","e","o","ma","anche","come","più","meno","molto","poco","tutto","niente",
    "nulla","essere","avere","fare","dire","andare","venire","dare","stare","potere",
    "dovere","volere","sapere","vedere","trovare","tenere","mettere","parlare","credere",
    "portare","lasciare","passare","pensare","guardare","tornare","sembrare","sentire",
    "restare","prendere","entrare","vivere","capire","ricordare","finire","arrivare",
    "scrivere","leggere","mangiare","bere","lavorare","studiare","giocare","correre",
    "camminare","aprire","chiudere","iniziare","continuare","cambiare","aiutare",
    "costruire","comprare","vendere","pagare","ricevere","mandare","trovare","perdere",
    "vincere","pensiero","tempo","anno","giorno","settimana","mese","vita","mondo",
    "scuola","stato","famiglia","studente","gruppo","paese","problema","mano","parte",
    "luogo","caso","punto","governo","azienda","numero","sistema","lavoro","programma",
    "domanda","fatto","casa","acqua","stanza","madre","padre","area","soldi","storia",
    "questione","lato","tipo","testa","servizio","amico","potere","ora","gioco","linea",
    "fine","membro","legge","auto","città","comunità","nome","presidente","squadra",
    "minuto","idea","bambino","corpo","informazione","schiena","genitore","faccia",
    "livello","ufficio","porta","salute","persona","arte","guerra","storia","partito",
    "risultato","cambiamento","mattina","ragione","ricerca","ragazza","ragazzo",
    "momento","aria","insegnante","forza","educazione","piede","politica","processo",
    "musica","mercato","senso","nazione","piano","interesse","morte","esperienza",
    "effetto","uso","utile","usato","usare","fare","fatto","fare","prendere","preso",
    "dare","dato","andare","andato","venire","venuto","vedere","visto","sapere","saputo",
    "pensare","pensato","credere","creduto","trovare","trovato","lasciare","lasciato",
    "sentire","sentito","entrare","entrato","vivere","vissuto","capire","capito",
    "scrivere","scritto","leggere","letto","aprire","aperto","chiudere","chiuso",
    "pagare","pagato","ricevere","ricevuto","perdere","perso","vincere","vinto"
}
# ---------------- FRENCH ----------------
LANG_WORDS["fr"] = {
    "le","la","les","un","une","des","du","de","à","au","aux","et","ou","mais","donc",
    "or","ni","car","que","qui","quoi","dont","où","quand","comment","pourquoi",
    "je","tu","il","elle","nous","vous","ils","elles","me","te","se","lui","leur",
    "mon","ma","mes","ton","ta","tes","son","sa","ses","notre","votre","leurs",
    "être","avoir","faire","dire","aller","venir","voir","savoir","pouvoir","vouloir",
    "devoir","prendre","donner","mettre","tenir","parler","croire","porter","laisser",
    "passer","penser","regarder","revenir","sembler","sentir","rester","entrer",
    "vivre","comprendre","rappeler","finir","arriver","écrire","lire","manger","boire",
    "travailler","étudier","jouer","courir","marcher","ouvrir","fermer","commencer",
    "continuer","changer","aider","construire","acheter","vendre","payer","recevoir",
    "perdre","gagner","temps","année","jour","semaine","mois","vie","monde","école",
    "état","famille","étudiant","groupe","pays","problème","main","partie","lieu",
    "cas","point","gouvernement","entreprise","nombre","système","travail","programme",
    "question","fait","maison","eau","pièce","mère","père","zone","argent","histoire",
    "question","côté","genre","tête","service","ami","pouvoir","heure","jeu","ligne",
    "fin","membre","loi","voiture","ville","communauté","nom","président","équipe",
    "minute","idée","enfant","corps","information","dos","parent","visage","niveau",
    "bureau","porte","santé","personne","art","guerre","parti","résultat","changement",
    "matin","raison","recherche","fille","garçon","moment","air","enseignant","force",
    "éducation","pied","politique","processus","musique","marché","sens","nation",
    "plan","intérêt","mort","expérience","effet","utilisation","utile","utiliser",
    "fait","pris","donné","allé","venu","vu","su","pensé","cru","trouvé","laissé",
    "senti","entré","vécu","compris","écrit","lu","ouvert","fermé","payé","reçu",
    "perdu","gagné","toujours","souvent","jamais","parfois","ici","là","ainsi","alors",
    "encore","déjà","très","trop","assez","peu","beaucoup","plus","moins","tout",
    "rien","quelque","chaque","autre","même","tel","tellement","ainsi","ceci","cela",
    "celui","celle","ceux","celles"
}

# ---------------- SPANISH ----------------
LANG_WORDS["es"] = {
    "el","la","los","las","un","una","unos","unas","de","a","en","con","por","para",
    "sobre","entre","y","o","pero","porque","aunque","si","cuando","donde","como",
    "yo","tú","él","ella","nosotros","vosotros","ellos","ellas","me","te","se","le",
    "les","mi","mis","tu","tus","su","sus","nuestro","vuestro","ser","estar","tener",
    "hacer","decir","ir","venir","ver","saber","poder","querer","deber","tomar",
    "dar","poner","mantener","hablar","creer","llevar","dejar","pasar","pensar",
    "mirar","volver","parecer","sentir","quedar","entrar","vivir","entender",
    "recordar","terminar","llegar","escribir","leer","comer","beber","trabajar",
    "estudiar","jugar","correr","caminar","abrir","cerrar","empezar","continuar",
    "cambiar","ayudar","construir","comprar","vender","pagar","recibir","perder",
    "ganar","tiempo","año","día","semana","mes","vida","mundo","escuela","estado",
    "familia","estudiante","grupo","país","problema","mano","parte","lugar","caso",
    "punto","gobierno","empresa","número","sistema","trabajo","programa","pregunta",
    "hecho","casa","agua","habitación","madre","padre","zona","dinero","historia",
    "lado","tipo","cabeza","servicio","amigo","poder","hora","juego","línea","fin",
    "miembro","ley","coche","ciudad","comunidad","nombre","presidente","equipo",
    "minuto","idea","niño","cuerpo","información","espalda","padre","cara","nivel",
    "oficina","puerta","salud","persona","arte","guerra","partido","resultado",
    "cambio","mañana","razón","investigación","chica","chico","momento","aire",
    "profesor","fuerza","educación","pie","política","proceso","música","mercado",
    "sentido","nación","plan","interés","muerte","experiencia","efecto","uso","útil",
    "usar","hecho","tomado","dado","ido","venido","visto","sabido","pensado",
    "creído","encontrado","dejado","sentido","entrado","vivido","entendido",
    "escrito","leído","abierto","cerrado","pagado","recibido","perdido","ganado",
    "siempre","a menudo","nunca","a veces","aquí","allí","así","entonces","todavía",
    "ya","muy","demasiado","bastante","poco","mucho","más","menos","todo","nada",
    "algún","cada","otro","mismo","tal","tanto","esto","eso","aquel","quien",
    "cual","cuales","cuyo","cuya"
}
# ---------------- GERMAN ----------------
LANG_WORDS["de"] = {
    "der","die","das","ein","eine","einer","eines","einem","den","dem","des",
    "und","oder","aber","denn","doch","sondern","weil","wenn","dass","ob",
    "wer","was","wann","wo","warum","wie","ich","du","er","sie","es","wir","ihr",
    "mich","dich","sich","mir","dir","ihm","ihr","uns","euch","mein","meine",
    "dein","deine","sein","seine","ihr","ihre","unser","unsere","haben","sein",
    "werden","machen","sagen","gehen","kommen","sehen","wissen","können",
    "wollen","müssen","nehmen","geben","legen","halten","sprechen","glauben",
    "tragen","lassen","passieren","denken","schauen","zurückkommen","scheinen",
    "fühlen","bleiben","eintreten","leben","verstehen","erinnern","beenden",
    "ankommen","schreiben","lesen","essen","trinken","arbeiten","lernen","spielen",
    "laufen","gehen","öffnen","schließen","anfangen","fortsetzen","ändern","helfen",
    "bauen","kaufen","verkaufen","bezahlen","erhalten","verlieren","gewinnen",
    "zeit","jahr","tag","woche","monat","leben","welt","schule","staat","familie",
    "student","gruppe","land","problem","hand","teil","ort","fall","punkt",
    "regierung","firma","zahl","system","arbeit","programm","frage","tatsache",
    "haus","wasser","zimmer","mutter","vater","bereich","geld","geschichte",
    "seite","art","kopf","dienst","freund","macht","stunde","spiel","linie",
    "ende","mitglied","gesetz","auto","stadt","gemeinschaft","name","präsident",
    "team","minute","idee","kind","körper","information","rücken","eltern",
    "gesicht","niveau","büro","tür","gesundheit","person","kunst","krieg","partei",
    "ergebnis","änderung","morgen","grund","forschung","mädchen","junge","moment",
    "luft","lehrer","kraft","bildung","fuß","politik","prozess","musik","markt",
    "sinn","nation","plan","interesse","tod","erfahrung","wirkung","nutzung",
    "nützlich","immer","oft","nie","manchmal","hier","dort","so","dann","noch",
    "schon","sehr","zu","genug","wenig","viel","mehr","weniger","alles","nichts",
    "etwas","jeder","andere","gleich","solch","dies","das","jener","welcher",
    "welche","dessen","deren"
}

# ---------------- PORTUGUESE ----------------
LANG_WORDS["pt"] = {
    "o","a","os","as","um","uma","uns","umas","de","do","da","dos","das","em","no",
    "na","nos","nas","por","para","com","sobre","entre","e","ou","mas","porque",
    "embora","se","quando","onde","como","eu","tu","ele","ela","nós","vós","eles",
    "elas","me","te","se","lhe","lhes","meu","minha","meus","minhas","teu","tua",
    "seu","sua","nosso","nossa","ser","estar","ter","fazer","dizer","ir","vir",
    "ver","saber","poder","querer","dever","tomar","dar","colocar","manter",
    "falar","acreditar","levar","deixar","passar","pensar","olhar","voltar",
    "parecer","sentir","ficar","entrar","viver","entender","lembrar","terminar",
    "chegar","escrever","ler","comer","beber","trabalhar","estudar","jogar",
    "correr","andar","abrir","fechar","começar","continuar","mudar","ajudar",
    "construir","comprar","vender","pagar","receber","perder","ganhar","tempo",
    "ano","dia","semana","mês","vida","mundo","escola","estado","família",
    "estudante","grupo","país","problema","mão","parte","lugar","caso","ponto",
    "governo","empresa","número","sistema","trabalho","programa","pergunta",
    "fato","casa","água","quarto","mãe","pai","zona","dinheiro","história","lado",
    "tipo","cabeça","serviço","amigo","poder","hora","jogo","linha","fim",
    "membro","lei","carro","cidade","comunidade","nome","presidente","equipe",
    "minuto","ideia","criança","corpo","informação","costas","pais","rosto",
    "nível","escritório","porta","saúde","pessoa","arte","guerra","partido",
    "resultado","mudança","manhã","razão","pesquisa","menina","menino","momento",
    "ar","professor","força","educação","pé","política","processo","música",
    "mercado","sentido","nação","plano","interesse","morte","experiência","efeito",
    "uso","útil","usar","sempre","frequentemente","nunca","às vezes","aqui","ali",
    "assim","então","ainda","já","muito","demais","bastante","pouco","mais",
    "menos","tudo","nada","algum","cada","outro","mesmo","tal","tanto","isto",
    "isso","aquele","quem","qual","quais","cujo","cuja"
}
# ---------------- DUTCH ----------------
LANG_WORDS["nl"] = {
    "de","het","een","en","of","maar","want","dus","dat","die","dit","wie","wat",
    "waar","wanneer","waarom","hoe","ik","jij","je","hij","zij","ze","wij","we",
    "jullie","hen","hem","haar","mijn","mijne","jouw","jouwe","zijn","zijne",
    "haar","hare","ons","onze","hun","hebben","zijn","worden","doen","zeggen",
    "gaan","komen","zien","weten","kunnen","willen","moeten","nemen","geven",
    "leggen","houden","spreken","geloven","dragen","laten","gebeuren","denken",
    "kijken","terugkomen","lijken","voelen","blijven","binnenkomen","leven",
    "begrijpen","herinneren","eindigen","aankomen","schrijven","lezen","eten",
    "drinken","werken","leren","spelen","rennen","lopen","openen","sluiten",
    "beginnen","doorgaan","veranderen","helpen","bouwen","kopen","verkopen",
    "betalen","ontvangen","verliezen","winnen","tijd","jaar","dag","week","maand",
    "leven","wereld","school","staat","familie","student","groep","land",
    "probleem","hand","deel","plaats","geval","punt","regering","bedrijf",
    "nummer","systeem","werk","programma","vraag","feit","huis","water","kamer",
    "moeder","vader","gebied","geld","geschiedenis","kant","soort","hoofd",
    "dienst","vriend","macht","uur","spel","lijn","einde","lid","wet","auto",
    "stad","gemeenschap","naam","president","team","minuut","idee","kind",
    "lichaam","informatie","rug","ouders","gezicht","niveau","kantoor","deur",
    "gezondheid","persoon","kunst","oorlog","partij","resultaat","verandering",
    "ochtend","reden","onderzoek","meisje","jongen","moment","lucht","leraar",
    "kracht","opleiding","voet","politiek","proces","muziek","markt","zin",
    "natie","plan","belang","dood","ervaring","effect","gebruik","altijd",
    "vaak","nooit","soms","hier","daar","zo","dan","nog","al","zeer","te","genoeg",
    "weinig","veel","meer","minder","alles","niets","iets","elk","andere",
    "zelfde","zulk","deze","dat","die","welke","wiens"
}

# ---------------- SWEDISH ----------------
LANG_WORDS["sv"] = {
    "en","ett","och","eller","men","för","att","som","det","den","de","vad","vem",
    "var","när","varför","hur","jag","du","han","hon","vi","ni","de","mig","dig",
    "honom","henne","oss","er","min","mitt","mina","din","ditt","dina","sin",
    "sitt","sina","vår","vårt","våra","har","är","blir","gör","säger","går",
    "kommer","ser","vet","kan","vill","måste","tar","ger","lägger","håller",
    "talar","tror","bär","låter","händer","tänker","tittar","återkommer","verkar",
    "känner","stannar","kommer in","lever","förstår","minns","slutar","anländer",
    "skriver","läser","äter","dricker","arbetar","studerar","spelar","springer",
    "går","öppnar","stänger","börjar","fortsätter","ändrar","hjälper","bygger",
    "köper","säljer","betalar","får","förlorar","vinner","tid","år","dag","vecka",
    "månad","liv","värld","skola","stat","familj","student","grupp","land",
    "problem","hand","del","plats","fall","punkt","regering","företag","nummer",
    "system","arbete","program","fråga","fakta","hus","vatten","rum","mor","far",
    "område","pengar","historia","sida","typ","huvud","tjänst","vän","makt",
    "timme","spel","linje","slut","medlem","lag","bil","stad","samhälle","namn",
    "president","lag","minut","idé","barn","kropp","information","rygg","föräldrar",
    "ansikte","nivå","kontor","dörr","hälsa","person","konst","krig","parti",
    "resultat","förändring","morgon","anledning","forskning","flicka","pojke",
    "ögonblick","luft","lärare","kraft","utbildning","fot","politik","process",
    "musik","marknad","känsla","nation","plan","intresse","död","erfarenhet",
    "effekt","användning","alltid","ofta","aldrig","ibland","här","där","så",
    "då","ännu","redan","mycket","för","nog","lite","många","mer","mindre",
    "allt","inget","något","varje","annan","samma","sådan","detta","denna",
    "vilken","vems"
}
# ---------------- POLISH ----------------
LANG_WORDS["pl"] = {
    "i","oraz","albo","ale","bo","ponieważ","że","aby","jak","kiedy","gdzie","dlaczego",
    "ja","ty","on","ona","ono","my","wy","oni","one","mnie","tobie","jemu","jej","nam",
    "wam","im","mój","moja","moje","twój","twoja","twoje","jego","jej","nasz","wasz",
    "być","mieć","robić","mówić","iść","przyjść","widzieć","wiedzieć","móc","chcieć",
    "musieć","brać","dać","kłaść","trzymać","rozmawiać","wierzyć","nosić","zostawić",
    "dziać","myśleć","patrzeć","wracać","wydawać","czuć","zostać","wejść","żyć",
    "rozumieć","pamiętać","kończyć","przybyć","pisać","czytać","jeść","pić","pracować",
    "uczyć","grać","biegać","chodzić","otworzyć","zamknąć","zaczynać","kontynuować",
    "zmieniać","pomagać","budować","kupować","sprzedawać","płacić","otrzymywać",
    "tracić","wygrywać","czas","rok","dzień","tydzień","miesiąc","życie","świat",
    "szkoła","państwo","rodzina","student","grupa","kraj","problem","ręka","część",
    "miejsce","przypadek","punkt","rząd","firma","liczba","system","praca","program",
    "pytanie","fakt","dom","woda","pokój","matka","ojciec","obszar","pieniądze",
    "historia","strona","rodzaj","głowa","usługa","przyjaciel","władza","godzina",
    "gra","linia","koniec","członek","prawo","samochód","miasto","społeczność","nazwa",
    "prezydent","zespół","minuta","pomysł","dziecko","ciało","informacja","plecy",
    "rodzice","twarz","poziom","biuro","drzwi","zdrowie","osoba","sztuka","wojna",
    "partia","wynik","zmiana","poranek","powód","badanie","dziewczyna","chłopak",
    "moment","powietrze","nauczyciel","siła","edukacja","stopa","polityka","proces",
    "muzyka","rynek","sens","naród","plan","interes","śmierć","doświadczenie","efekt",
    "użycie","zawsze","często","nigdy","czasami","tu","tam","tak","wtedy","jeszcze",
    "już","bardzo","za","wystarczająco","mało","dużo","więcej","mniej","wszystko",
    "nic","coś","każdy","inny","ten","ta","to","który","czyj","czyja","czyje","oraz",
    "ponadto","przecież","natomiast","również","różny","różnie","właśnie","prawie",
    "około","blisko","daleko","wcześniej","później","zanim","potem","teraz","dzisiaj",
    "jutro","wczoraj","nadal","zwykle","rzadko","nagle","powoli","szybko","łatwo",
    "trudno","ważny","istotny","główny","lokalny","publiczny","prywatny","nowy","stary",
    "duży","mały","pierwszy","ostatni","lepszy","gorszy","prawdziwy","fałszywy"
}

# ---------------- RUSSIAN ----------------
LANG_WORDS["ru"] = {
    "и","или","но","потому","что","чтобы","как","когда","где","почему","я","ты","он",
    "она","оно","мы","вы","они","меня","тебя","его","её","нас","вас","их","мой","моя",
    "моё","твой","твоя","твоё","его","её","наш","ваш","быть","иметь","делать","говорить",
    "идти","прийти","видеть","знать","мочь","хотеть","должен","брать","давать","класть",
    "держать","говорить","верить","носить","оставлять","происходить","думать","смотреть",
    "возвращаться","казаться","чувствовать","оставаться","входить","жить","понимать",
    "помнить","заканчивать","прибывать","писать","читать","есть","пить","работать",
    "учиться","играть","бегать","ходить","открывать","закрывать","начинать","продолжать",
    "менять","помогать","строить","покупать","продавать","платить","получать","терять",
    "выигрывать","время","год","день","неделя","месяц","жизнь","мир","школа","государство",
    "семья","студент","группа","страна","проблема","рука","часть","место","случай",
    "точка","правительство","компания","число","система","работа","программа","вопрос",
    "факт","дом","вода","комната","мать","отец","область","деньги","история","сторона",
    "тип","голова","служба","друг","власть","час","игра","линия","конец","член","закон",
    "машина","город","сообщество","имя","президент","команда","минута","идея","ребёнок",
    "тело","информация","спина","родители","лицо","уровень","офис","дверь","здоровье",
    "человек","искусство","война","партия","результат","изменение","утро","причина",
    "исследование","девочка","мальчик","момент","воздух","учитель","сила","образование",
    "нога","политика","процесс","музыка","рынок","смысл","нация","план","интерес",
    "смерть","опыт","эффект","использование","всегда","часто","никогда","иногда","здесь",
    "там","так","тогда","ещё","уже","очень","слишком","достаточно","мало","много","больше",
    "меньше","всё","ничего","что-то","каждый","другой","этот","эта","это","который",
    "чей","чья","чьё","также","поэтому","однако","кроме","примерно","почти","около",
    "близко","далеко","раньше","позже","перед","после","сейчас","сегодня","завтра",
    "вчера","обычно","редко","внезапно","медленно","быстро","легко","трудно","важный",
    "основной","местный","общественный","частный","новый","старый","большой","маленький",
    "первый","последний","лучше","хуже","правильный","неверный"
}
# ---------------- GREEK ----------------
LANG_WORDS["el"] = {
    "και","ή","αλλά","όμως","γιατί","ότι","πως","αν","όταν","πού","πότε","πώς",
    "εγώ","εσύ","αυτός","αυτή","αυτό","εμείς","εσείς","αυτοί","με","σε","τον","την",
    "μας","σας","τους","μου","σου","του","της","μας","σας","είμαι","έχω","κάνω",
    "λέω","πάω","έρχομαι","βλέπω","ξέρω","μπορώ","θέλω","πρέπει","παίρνω","δίνω",
    "βάζω","κρατώ","μιλώ","πιστεύω","φοράω","αφήνω","συμβαίνει","σκέφτομαι",
    "κοιτάζω","επιστρέφω","φαίνομαι","νιώθω","μένω","μπαίνω","ζω","καταλαβαίνω",
    "θυμάμαι","τελειώνω","φτάνω","γράφω","διαβάζω","τρώω","πίνω","δουλεύω",
    "μαθαίνω","παίζω","τρέχω","περπατώ","ανοίγω","κλείνω","αρχίζω","συνεχίζω",
    "αλλάζω","βοηθώ","χτίζω","αγοράζω","πουλάω","πληρώνω","παίρνω","χάνω","κερδίζω",
    "χρόνος","έτος","μέρα","εβδομάδα","μήνας","ζωή","κόσμος","σχολείο","κράτος",
    "οικογένεια","φοιτητής","ομάδα","χώρα","πρόβλημα","χέρι","μέρος","τόπος",
    "περίπτωση","σημείο","κυβέρνηση","εταιρεία","αριθμός","σύστημα","εργασία",
    "πρόγραμμα","ερώτηση","γεγονός","σπίτι","νερό","δωμάτιο","μητέρα","πατέρας",
    "περιοχή","χρήματα","ιστορία","πλευρά","τύπος","κεφάλι","υπηρεσία","φίλος",
    "δύναμη","ώρα","παιχνίδι","γραμμή","τέλος","μέλος","νόμος","αυτοκίνητο","πόλη",
    "κοινότητα","όνομα","πρόεδρος","ομάδα","λεπτό","ιδέα","παιδί","σώμα",
    "πληροφορία","πλάτη","γονείς","πρόσωπο","επίπεδο","γραφείο","πόρτα","υγεία",
    "άτομο","τέχνη","πόλεμος","κόμμα","αποτέλεσμα","αλλαγή","πρωί","λόγος",
    "έρευνα","κορίτσι","αγόρι","στιγμή","αέρας","δάσκαλος","δύναμη","εκπαίδευση",
    "πόδι","πολιτική","διαδικασία","μουσική","αγορά","νόημα","έθνος","σχέδιο",
    "ενδιαφέρον","θάνατος","εμπειρία","επίδραση","χρήση","πάντα","συχνά","ποτέ",
    "μερικές","εδώ","εκεί","έτσι","τότε","ακόμη","ήδη","πολύ","λίγο","αρκετά",
    "περισσότερο","λιγότερο","όλα","τίποτα","κάτι","κάθε","άλλος","ίδιος","τέτοιος"
}

# ---------------- TURKISH ----------------
LANG_WORDS["tr"] = {
    "ve","veya","ama","çünkü","ki","eğer","ne","kim","nerede","ne zaman","neden",
    "nasıl","ben","sen","o","biz","siz","onlar","beni","seni","onu","bizi","sizi",
    "onları","benim","senin","onun","bizim","sizin","olmak","sahip","yapmak",
    "demek","gitmek","gelmek","görmek","bilmek","yapabilmek","istemek","zorunda",
    "almak","vermek","koymak","tutmak","konuşmak","inanmak","taşımak","bırakmak",
    "olmak","düşünmek","bakmak","dönmek","görünmek","hissetmek","kalmak","girmek",
    "yaşamak","anlamak","hatırlamak","bitirmek","varmak","yazmak","okumak",
    "yemek","içmek","çalışmak","öğrenmek","oynamak","koşmak","yürümek","açmak",
    "kapatmak","başlamak","devam","değiştirmek","yardım","inşa","satın","satmak",
    "ödemek","almak","kaybetmek","kazanmak","zaman","yıl","gün","hafta","ay",
    "hayat","dünya","okul","devlet","aile","öğrenci","grup","ülke","problem","el",
    "parça","yer","durum","nokta","hükümet","şirket","sayı","sistem","iş","program",
    "soru","gerçek","ev","su","oda","anne","baba","bölge","para","tarih","taraf",
    "tür","kafa","hizmet","arkadaş","güç","saat","oyun","çizgi","son","üye","kanun",
    "araba","şehir","toplum","isim","başkan","takım","dakika","fikir","çocuk",
    "vücut","bilgi","sırt","ebeveyn","yüz","seviye","ofis","kapı","sağlık","kişi",
    "sanat","savaş","parti","sonuç","değişim","sabah","neden","araştırma","kız",
    "erkek","an","hava","öğretmen","kuvvet","eğitim","ayak","politika","süreç",
    "müzik","pazar","anlam","millet","plan","ilgi","ölüm","deneyim","etki",
    "kullanım","her zaman","sık","asla","bazen","burada","orada","böyle","sonra",
    "hala","zaten","çok","az","yeterli","fazla","daha","daha az","her şey","hiçbir",
    "bir şey","her","diğer","aynı","böyle"
}

# ---------------- ARABIC (MSA, TRANSLITERATED) ----------------
LANG_WORDS["ar"] = {
    "wa","aw","lakin","lianna","anna","idha","man","ma","ayna","mata","ayna",
    "limadha","kayfa","ana","anta","anti","huwa","hiya","nahnu","antum","hum",
    "li","laka","laki","lahu","laha","lana","lakum","lahum","kawn","yakun","kana",
    "ladayhi","faala","qala","dhahaba","ata","raaa","alama","istataa","arada",
    "yajibu","akhadha","aataa","wadaa","amsaka","takallama","amana","hamala",
    "taraka","hadatha","fakkara","nazara","rajaa","badat","shaara","baqiya",
    "dakhala","aasha","fahima","tadhakkara","intahaa","wasala","kataba","qaraa",
    "akala","shariba","amila","taallama","laaiba","rakada","mashaa","fataha",
    "aghlaqa","badaa","istamara","ghayyara","saada","banaa","ishtaraa","baaa",
    "dafaa","istalama","khasira","rabiha","waqt","sana","yawm","usbua","shahr",
    "hayat","aalam","madrasa","dawla","aaila","talib","majmua","balad","mushkila",
    "yad","juz","makan","hala","nuqta","hukuma","sharika","raqam","nitham","amal",
    "barnamaj","suual","haqiqa","bayt","maa","ghurfa","umm","ab","mintaqa","mal",
    "tarikh","janib","naw","raas","khidma","sadiq","quwwa","saa","laaiba","khat",
    "nihaya","uww","qanun","sayara","madina","mujtamaa","ism","raees","fariq",
    "daqeeqa","fikra","tifl","jasad","malumat","dhahr","walidayn","wajh","mustawa",
    "maktab","bab","sihha","shakhs","fann","harb","hizb","natija","taghyir",
    "sabah","sabab","bahth","bint","walad","lahtha","hawa","mudarris","qudra",
    "taalim","qadam","siyasa","amaliyya","musiqa","suq","maana","umma","khatta",
    "ihtimam","mawt","tajriba","athar","istikhdaam","daiman","kathiran","abadan",
    "ahyana","huna","hunak","hakadha","thumma","baad","hala","qad","kathir","qaleel",
    "akthar","aqall","kull","shay","baad","kul","akhar","nafs","mithl"
}

# ---------------- JAPANESE (ROMAJI) ----------------
LANG_WORDS["ja"] = {
    "soshite","mata","demo","dakara","naze","itsu","doko","dare","nani","dou",
    "watashi","anata","kare","kanojo","watashitachi","anatatachi","karera",
    "kore","sore","are","koko","soko","asoko","kono","sono","ano","aru","iru",
    "suru","iu","iku","kuru","miru","shiru","dekiru","hoshii","nakereba","toru",
    "ageru","oku","motsu","hanasu","shinjiru","haku","hanasu","omou","miru",
    "modoru","kanjiru","nokoru","hairu","ikiru","wakaru","oboeru","owaru",
    "tsuku","kaku","yomu","taberu","nomu","hataraku","manabu","asobu","hashiru",
    "aruku","akeru","shimeru","hajimeru","tsuzukeru","kaeru","tasukeru",
    "tateru","kau","uru","harau","ukeru","ushinau","katsu","jikan","toshi",
    "hi","shuukan","tsuki","inochi","sekai","gakkou","kuni","kazoku","gakusei",
    "gurupu","kuni","mondai","te","bubun","basho","baai","pointo","seifu",
    "kaisha","bangou","shisutemu","shigoto","puroguramu","shitsumon","jijitsu",
    "ie","mizu","heya","haha","chichi","chiiki","okane","rekishi","men","shurui",
    "atama","saabisu","tomodachi","chikara","jikan","geemu","sen","owari",
    "menbaa","hou","kuruma","machi","komyuniti","namae","daitouryou","chiimu",
    "fun","idea","kodomo","karada","jouhou","senaka","oya","kao","reberu",
    "ofisu","doa","kenkou","hito","aato","sensou","tou","kekka","henka",
    "asa","riyuu","kenkyuu","onna","otoko","shunkan","kuuki","sensei",
    "chikara","kyouiku","ashi","seiji","purosesu","ongaku","ichiba",
    "imi","kokka","keikaku","kyoumi","shi","keiken","kouka","riyuu",
    "itsumo","yoku","zenzen","tokidoki","koko","soko","sou","sorekara",
    "mada","mou","totemo","sukoshi","juubun","takusan","motto","sukunai",
    "subete","nanimo","nanika","daremo","hoka","onaji","konna"
}
# ---------------- CHINESE (PINYIN) ----------------
LANG_WORDS["zh"] = {
    "de","le","shi","bu","wo","ni","ta","women","nimen","tamen","zhe","na","zai",
    "you","mei","hen","ye","he","erqie","danshi","yinwei","suoyi","shenme","shei",
    "nali","shenme","shihou","weishenme","zenme","qu","lai","kan","zhidao","keyi",
    "xiang","yao","yinggai","na","gei","fang","chi","he","xuexi","gongzuo",
    "youxi","zou","pao","kai","guan","kaishi","jixu","gaibian","bangzhu","jianli",
    "mai","mai","fu","shoudao","shiqu","ying","shijian","nian","ri","zhou","yue",
    "shenghuo","shijie","xuexiao","guojia","jiating","xuesheng","qunti","guojia",
    "wenti","shou","bufen","difang","qingkuang","dian","zhengfu","gongsi",
    "shuzi","xitong","gongzuo","chengxu","wenti","shishi","fangzi","shui",
    "fangjian","mama","baba","diqu","qian","lishi","fangmian","leixing","toubu",
    "fuwu","pengyou","liliang","xiaoshi","youxi","xian","jieshu","chengyuan",
    "falv","qiche","chengshi","shequ","mingzi","zongtong","tuandui","fenzhong",
    "zhuyi","haizi","shenti","xinxi","beibu","fumu","lian","shuiping","bangongshi",
    "men","jiankang","ren","yishu","zhanzheng","dang","jieguo","bianhua","zaoshang",
    "yuanyin","yanjiu","nuhai","nanhai","shunjian","kongqi","laoshi","nengli",
    "jiaoyu","jiao","zhengzhi","guocheng","yinyue","shichang","yisi","minzu",
    "jihua","xingqu","siwang","jingyan","xiaoguo","shiyong","zongshi","changchang",
    "congbu","youzhi","zheli","nali","zheyang","ranzhou","hai","yijing","feichang",
    "shaoxu","gou","henduo","gengduo","gengshao","quanbu","shenme","renhe","mei",
    "mei","qita","tongyang","zheyang"
}

# ---------------- KOREAN (ROMANIZED) ----------------
LANG_WORDS["ko"] = {
    "geurigo","ttoneun","hajiman","geuraeseo","wae","eonje","eodi","nugu","mueot",
    "eotteoke","na","neo","geu","geunyeo","uri","neohui","geudeul","igeot","geugeot",
    "jeogeot","issda","eopda","hada","malhada","gada","oda","boda","alda","hal",
    "sipda","haeya","gatda","juda","noe","jida","sseuda","deulda","saenggakhada",
    "dorogada","neukkida","namda","deulda","sald","alga","gieokhada","kkeutnada",
    "dochagada","sseuda","ilgda","meokda","masida","il하다","gongbuhada","nol다",
    "dallida","geotda","yeolda","datda","sijakhada","gyesokhada","bakkuda",
    "dowajuda","jilda","sada","palda","jibulhada","bad다","ilgoda","igotda",
    "sigan","nyeon","nal","ju","dal","salme","segye","hakgyo","nara","gajok",
    "haksaeng","jiphap","gukga","munje","son","bubun","jangso","sanghwang","jeom",
    "jeongbu","hoesa","suje","siseutem","il","peurogeuraem","jilmun","sasil","jib",
    "mul","bang","eomeoni","abeoji","jiyeok","don","yeoksa","yeop","jonglyu",
    "meori","seobiseu","chingu","him","sigan","geim","seon","kkeut","hoewon",
    "beop","cha","dosi","gongdongche","ireum","daetongryeong","tim","bun",
    "aideo","ai","mom","jeongbo","deung","bumo","eolgul","su","samu","mun","geongang",
    "saram","yesul","jeonjaeng","dang","gyeolgwa","byeonhwa","achim","iyu","yeongu",
    "sonyeo","sonyeon","sungan","gonggi","seonsaeng","him","gyoyuk","bal","jeongchi",
    "gwajeong","eumak","sijang","uimi","minjok","gyehoek","gwangsim","jug-eum",
    "gyeongheom","hyogwa","sayong","hangsang","jaju","jeoldae","gakkeum","yeogi",
    "geogi","geureoke","geuttae","ajik","beolsseo","aju","jogeum","chungbun",
    "mani","deo","jeokge","modeun","amugeotdo","mu-eon-ga","modeun","dareun",
    "gat-eun"
}

# ---------------- CZECH ----------------
LANG_WORDS["cs"] = {
    "a","nebo","ale","protože","že","aby","jak","kdy","kde","proč","já","ty","on",
    "ona","ono","my","vy","oni","mě","tě","ho","ji","nás","vás","jejich","můj",
    "moje","tvůj","jeho","její","náš","váš","být","mít","dělat","říkat","jít",
    "přijít","vidět","vědět","moci","chtít","muset","vzít","dát","položit","držet",
    "mluvit","věřit","nést","nechat","stát","myslet","dívat","vrátit","zdát",
    "cítit","zůstat","vstoupit","žít","rozumět","pamatovat","skončit","dorazit",
    "psát","číst","jíst","pít","pracovat","učit","hrát","běžet","chodit","otevřít",
    "zavřít","začít","pokračovat","změnit","pomoci","stavět","koupit","prodat",
    "platit","dostat","ztratit","vyhrát","čas","rok","den","týden","měsíc","život",
    "svět","škola","stát","rodina","student","skupina","země","problém","ruka",
    "část","místo","případ","bod","vláda","firma","číslo","systém","práce",
    "program","otázka","fakt","dům","voda","pokoj","matka","otec","oblast","peníze",
    "historie","strana","typ","hlava","služba","přítel","síla","hodina","hra","linie",
    "konec","člen","zákon","auto","město","komunita","jméno","prezident","tým",
    "minuta","nápad","dítě","tělo","informace","záda","rodiče","tvář","úroveň",
    "kancelář","dveře","zdraví","osoba","umění","válka","strana","výsledek","změna",
    "ráno","důvod","výzkum","dívka","chlapec","okamžik","vzduch","učitel","síla",
    "vzdělání","noha","politika","proces","hudba","trh","smysl","národ","plán",
    "zájem","smrt","zkušenost","efekt","použití"
}

# ---------------- HUNGARIAN ----------------
LANG_WORDS["hu"] = {
    "és","vagy","de","mert","hogy","ha","ki","mi","hol","mikor","miért","hogyan",
    "én","te","ő","mi","ti","ők","engem","téged","őt","minket","titeket","őket",
    "enyém","tiéd","övé","miénk","tietek","övék","lenni","van","csinál","mond",
    "megy","jön","lát","tud","képes","akar","kell","vesz","ad","tesz","tart",
    "beszél","hisz","visel","hagy","történik","gondol","néz","visszatér","érez",
    "marad","belép","él","ért","emlékszik","befejez","érkezik","ír","olvas","eszik",
    "iszik","dolgozik","tanul","játszik","fut","sétál","nyit","zár","kezd","folytat",
    "változtat","segít","épít","vásárol","elad","fizet","kap","elveszít","nyer",
    "idő","év","nap","hét","hónap","élet","világ","iskola","állam","család",
    "diák","csoport","ország","probléma","kéz","rész","hely","eset","pont","kormány",
    "cég","szám","rendszer","munka","program","kérdés","tény","ház","víz","szoba",
    "anya","apa","terület","pénz","történelem","oldal","típus","fej","szolgáltatás",
    "barát","erő","óra","játék","vonal","vég","tag","törvény","autó","város",
    "közösség","név","elnök","csapat","perc","ötlet","gyerek","test","információ",
    "hát","szülők","arc","szint","iroda","ajtó","egészség","személy","művészet",
    "háború","párt","eredmény","változás","reggel","ok","kutatás","lány","fiú",
    "pillanat","levegő","tanár","erő","oktatás","láb","politika","folyamat",
    "zene","piac","értelem","nemzet","terv","érdeklődés","halál","tapasztalat",
    "hatás","használat"
}

# ---------------- FINNISH ----------------
LANG_WORDS["fi"] = {
    "ja","tai","mutta","koska","että","jos","kuka","mikä","missä","milloin","miksi",
    "miten","minä","sinä","hän","me","te","he","minut","sinut","hänet","meidät",
    "teidät","heidät","minun","sinun","hänen","meidän","teidän","heidän","olla",
    "tehdä","sanoa","mennä","tulla","nähdä","tietää","voida","haluta","täytyä",
    "ottaa","antaa","laittaa","pitää","puhua","uskoa","kantaa","jättää","tapahtua",
    "ajatella","katsoa","palata","tuntua","pysyä","astua","elää","ymmärtää",
    "muistaa","lopettaa","saapua","kirjoittaa","lukea","syödä","juoda","työskennellä",
    "opiskella","pelata","juosta","kävellä","avata","sulkea","aloittaa","jatkaa",
    "muuttaa","auttaa","rakentaa","ostaa","myydä","maksaa","saada","menettää",
    "voittaa","aika","vuosi","päivä","viikko","kuukausi","elämä","maailma","koulu",
    "valtio","perhe","opiskelija","ryhmä","maa","ongelma","käsi","osa","paikka",
    "tapaus","piste","hallitus","yritys","numero","järjestelmä","työ","ohjelma",
    "kysymys","tosiasia","talo","vesi","huone","äiti","isä","alue","raha","historia",
    "puoli","tyyppi","pää","palvelu","ystävä","voima","tunti","peli","viiva","loppu",
    "jäsen","laki","auto","kaupunki","yhteisö","nimi","presidentti","tiimi",
    "minuutti","idea","lapsi","keho","tieto","selkä","vanhemmat","kasvot","taso",
    "toimisto","ovi","terveys","henkilö","taide","sota","puolue","tulos","muutos",
    "aamu","syy","tutkimus","tyttö","poika","hetki","ilma","opettaja","voima",
    "koulutus","jalka","politiikka","prosessi","musiikki","markkinat","merkitys",
    "kansa","suunnitelma","kiinnostus","kuolema","kokemus","vaikutus","käyttö"
}

# ---------------- HEBREW (TRANSLITERATED) ----------------
LANG_WORDS["he"] = {
    "ve","o","aval","ki","she","im","mi","ma","eifo","matai","lama","ech","ani",
    "ata","at","hu","hi","anachnu","atem","hen","oti","otcha","oto","ota","otanu",
    "otchem","otam","sheli","shelcha","shelo","shela","shelanu","shelachem",
    "lihiyot","yesh","asah","amar","halach","ba","raah","yada","yachol","ratsa",
    "tsarich","lakach","natan","sam","hechzik","diber","heemin","nasa","azav",
    "kara","chashav","hibit","chazar","hargish","nishar","nichnas","chaya","hevin",
    "zachar","siyem","higia","katav","kara","achal","shata","avad","lamad","sichek",
    "ratz","halach","patach","sagar","hechel","himshech","shina","azar","bana",
    "kana","machar","shilem","kibel","hibid","zacha","zman","shana","yom","shavua",
    "chodesh","chaim","olam","beitsefer","medina","mishpacha","student","kvutza",
    "aretz","baaya","yad","chelek","makom","mikre","nekuda","memshala","chevra",
    "mispar","maarechet","avoda","tochnit","sheela","ovda","bayit","mayim","cheder",
    "ima","aba","ezor","kesef","historia","tzad","sug","rosh","sherut","chaver",
    "koach","shaa","misxak","kav","sof","chaver","chok","mechonit","ir","kehilah",
    "shem","nasi","tsvat","daka","raayon","yeled","guf","meida","gav","horim",
    "panim","rama","misrad","delet","briut","adam","omanut","milchama","miflaga",
    "totsaah","shinui","boker","siba","mechkar","yalda","yeled","rega","avir",
    "more","koach","chinuch","regel","politika","tahalich","musika","shuk",
    "mashmaut","leom","tochnit","inyan","mavet","nisayon","hashpaa","shimush"
}
# ---------------- SESOTHO (SOUTHERN SOTHO) ----------------
LANG_WORDS["st"] = {
    "le","kapa","empa","hobane","hore","ha","mang","eng","hokae","neng","hobaneng",
    "jwang","nna","wena","ena","rona","lona","bona","ntja","ena","rona","lona",
    "bona","ya","tsa","ka","ho","ke","ba","na","hae","hao","hae","rona","lona",
    "bona","ba","ba","e","etsa","re","ya","tla","bona","tseba","kgona","batla",
    "lokela","nka","fa","beha","tshwara","bua","dumella","jara","tlohela","etsahala",
    "nahana","sheba","kgutla","utlwa","dula","kena","phela","utloisisa","hopola",
    "qeta","fihla","ngola","bala","ja","nwa","sebelisoa","ithuta","bapala","matha",
    "tsamaya","bula","kwala","qala","tswela","fetola","thusa","aha","reka","rekisa",
    "lefa","fumana","lahleheloa","hlola","nako","selemo","letsatsi","beke","kgwedi",
    "bophelo","lefatshe","sekolo","naha","lelapa","moithuti","sehlopha","naha",
    "bothata","letsoho","karolo","sebaka","boemo","ntlha","mmuso","khamphani",
    "nomoro","tsamaiso","mosebetsi","lenaneo","potso","nnete","ntlo","metsi",
    "kamore","mme","ntate","sebaka","tjhelete","nalane","lehlakore","mofuta",
    "hlooho","tshebeletso","motsoalle","matla","hora","papadi","mola","qetello",
    "setho","molao","koloi","toropo","setjhaba","lebitso","mopresidente","sehlopha",
    "metsotso","mohoo","ngwana","mmele","tlhahisoleseding","mokokotlo","batsoali",
    "sefahleho","boemo","ofisi","monyako","bophelo","motho","bonono","ntwa",
    "mokha","sephetho","phetoho","hoseng","lebaka","patlisiso","ngwanana",
    "ngwananyana","motsotso","moea","tichere","thuto","leoto","dipolotiki",
    "tshebetso","mino","mabenkele","moelelo","setjhaba","morero","thahasello",
    "lefu","phihlelo","phello","tshebediso","kamehla","hangata","le ka mohla",
    "ka dinako","mona","teng","jwalo","ebe","ntse","se","haholo","hanyane",
    "lekaneng","ho feta","ho fokola","tsohle","ha ho letho","ntho","mong le mong",
    "e mong","tshwana","jwalo"
}

# ---------------- SWAHILI ----------------
LANG_WORDS["sw"] = {
    "na","au","lakini","kwa sababu","kwamba","ikiwa","nani","nini","wapi","lini",
    "kwa nini","vipi","mimi","wewe","yeye","sisi","ninyi","wao","yangu","yako",
    "yake","yetu","yenu","yao","kuwa","kuwa na","fanya","sema","enda","kuja",
    "ona","jua","weza","taka","lazima","chukua","toa","weka","shika","zungumza",
    "amini","beba","acha","tokea","fikiria","tazama","rudi","hisia","baki","ingia",
    "ishi","elewa","kumbuka","maliza","fika","andika","soma","kula","kunywa",
    "fanya kazi","jifunza","cheza","kimbia","tembea","fungua","funga","anza",
    "endelea","badilisha","saidia","jenga","nunua","uza","lipa","pokea","poteza",
    "shinda","wakati","mwaka","siku","wiki","mwezi","maisha","dunia","shule",
    "serikali","familia","mwanafunzi","kikundi","nchi","tatizo","mkono","sehemu",
    "mahali","hali","alama","kampuni","namba","mfumo","kazi","programu","swali",
    "ukweli","nyumba","maji","chumba","mama","baba","eneo","pesa","historia",
    "upande","aina","kichwa","huduma","rafiki","nguvu","saa","mchezo","mstari",
    "mwisho","mwanachama","sheria","gari","jiji","jamii","jina","rais","timu",
    "dakika","wazo","mtoto","mwili","taarifa","mgongo","wazazi","uso","kiwango",
    "ofisi","mlango","afya","mtu","sanaa","vita","chama","matokeo","mabadiliko",
    "asubuhi","sababu","utafiti","msichana","mvulana","wakati","hewa","mwalimu",
    "elimu","mguu","siasa","mchakato","muziki","soko","maana","taifa","mpango",
    "nia","kifo","uzoefu","athari","matumizi","daima","mara nyingi","kamwe",
    "wakati mwingine","hapa","pale","hivyo","kisha","bado","tayari","sana",
    "kidogo","kutosha","zaidi","chini","kila kitu","hakuna","kitu","kila","mwingine"
}

# ---------------- ZULU ----------------
LANG_WORDS["zu"] = {
    "futhi","noma","kodwa","ngoba","ukuthi","uma","ubani","ini","kuphi","nini",
    "kungani","kanjani","mina","wena","yena","thina","nina","bona","wami","wakho",
    "wakhe","wethu","wenu","wabo","ukuba","ukuba na","enza","sho","hamba","za",
    "bona","azi","akwazi","funa","kumele","thatha","nika","beka","bamba","khuluma",
    "kholwa","phatha","shiya","kwenzeka","cabanga","buka","buya","zwa","hlala",
    "ngena","phila","qonda","khumbula","qeda","fika","bhala","funda","dla","phuza",
    "sebenza","funda","dlala","gijima","hamba","vula","vala","qala","qhubeka",
    "shintsha","siza","akha","thenga","thengisa","khokha","thola","lahlekelwa",
    "nqoba","isikhathi","unyaka","usuku","iviki","inyanga","impilo","umhlaba",
    "isikole","izwe","umndeni","umfundi","iqembu","izwe","inkinga","isandla",
    "ingxenye","indawo","isimo","iphuzu","uhulumeni","inkampani","inombolo",
    "uhlelo","umsebenzi","uhlelo","umbuzo","iqiniso","indlu","amanzi","igumbi",
    "umama","ubaba","indawo","imali","umlando","uhlangothi","uhlobo","ikhanda",
    "inkonzo","umngane","amandla","ihora","umdlalo","ulayini","isiphetho",
    "ilungu","umthetho","imoto","idolobha","umphakathi","igama","umongameli",
    "iqembu","imizuzu","umbono","ingane","umzimba","ulwazi","umhlane","abazali",
    "ubuso","izinga","ihhovisi","umnyango","impilo","umuntu","ubuciko","impi",
    "iqembu","umphumela","ushintsho","ekuseni","isizathu","ucwaningo","intombazane",
    "umfana","isikhathi","umoya","uthisha","imfundo","unyawo","ipolitiki",
    "inqubo","umculo","imakethe","incazelo","isizwe","uhlelo","intshisekelo",
    "ukufa","isipiliyoni","umthelela","ukusetshenziswa"
}

# ---------------- AFRIKAANS ----------------
LANG_WORDS["af"] = {
    "en","of","maar","want","dat","as","wie","wat","waar","wanneer","hoekom","hoe",
    "ek","jy","hy","sy","ons","julle","hulle","my","jou","hom","haar","ons","julle",
    "hulle","myne","joune","syne","hare","ons s'n","julle s'n","wees","hê","doen",
    "sê","gaan","kom","sien","weet","kan","wil","moet","neem","gee","sit","hou",
    "praat","glo","dra","los","gebeur","dink","kyk","terug","voel","bly","ingaan",
    "leef","verstaan","onthou","klaar","aankom","skryf","lees","eet","drink",
    "werk","leer","speel","hardloop","loop","oopmaak","toemaak","begin","aanhou",
    "verander","help","bou","koop","verkoop","betaal","kry","verloor","wen",
    "tyd","jaar","dag","week","maand","lewe","wêreld","skool","staat","familie",
    "student","groep","land","probleem","hand","deel","plek","geval","punt",
    "regering","maatskappy","nommer","stelsel","werk","program","vraag","feit",
    "huis","water","kamer","ma","pa","gebied","geld","geskiedenis","kant","tipe",
    "kop","diens","vriend","krag","uur","speletjie","lyn","einde","lid","wet",
    "motor","stad","gemeenskap","naam","president","span","minuut","idee","kind",
    "liggaam","inligting","rug","ouers","gesig","vlak","kantoor","deur","gesondheid",
    "persoon","kuns","oorlog","party","resultaat","verandering","oggend","rede",
    "navorsing","meisie","seun","oomblik","lug","onderwyser","onderwys","voet",
    "politiek","proses","musiek","mark","betekenis","nasie","plan","belangstelling",
    "dood","ervaring","effek","gebruik"
}

# ---------------- HAUSA ----------------
LANG_WORDS["ha"] = {
    "da","ko","amma","saboda","cewa","idan","wa","me","ina","yaya","ni","kai","shi",
    "ita","mu","ku","su","ni","ka","naka","naki","nashi","nata","nammu","naku",
    "nasu","kasance","da","yi","ce","tafi","zo","gani","sani","iya","so","dole",
    "dauka","ba","sanya","rike","yi magana","yarda","dauka","bar","faru","tuna",
    "kalli","koma","ji","zauna","shiga","rayu","fahimta","tuna","kare","isa",
    "rubuta","karanta","ci","sha","aiki","koyo","wasa","gudu","tafiya","bude",
    "rufe","fara","ci gaba","canza","taimaka","gina","saya","sayar","biya",
    "karba","rasa","ci nasara","lokaci","shekara","rana","mako","wata","rayuwa",
    "duniya","makaranta","kasa","iyali","dalibi","kungiya","kasa","matsala",
    "hannu","bangare","wuri","hali","alama","gwamnati","kamfani","lamba","tsari",
    "aiki","shiri","tambaya","gaskiya","gida","ruwa","daki","uwa","uba","yanki",
    "kudi","tarihi","gefe","nau'i","kai","sabis","aboki","karfi","awa","wasa",
    "layi","karshe","memba","doka","mota","birni","al'umma","suna","shugaba",
    "tawaga","minti","ra'ayi","yaro","jiki","bayani","baya","iyaye","fuska",
    "mataki","ofis","kofa","lafiya","mutum","fasaha","yaki","jam'iyya","sakamako",
    "canji","safe","dalili","bincike","yarinya","yaro","lokaci","iska","malami",
    "ilimi","kafa","siyasa","tsari","waka","kasuwa","ma'ana","kasa","shiri",
    "sha'awa","mutuwa","kwarewa","tasiri","amfani"
}

# ---------------- YORUBA (SIMPLIFIED) ----------------
LANG_WORDS["yo"] = {
    "ati","tabi","sugbon","nitori","pe","ti","ta","ibo","nigbawo","idi","bawo",
    "emi","iwo","oun","awa","eyin","awon","mi","re","un","wa","yin","won","tiemi",
    "tirẹ","tire","tiwa","tiyin","tiwon","je","ni","se","so","lo","wa","ri","mo",
    "le","fe","gbodo","gba","fun","fi","mu","soro","gba","ru","fi sile","sele",
    "ro","wo","pada","lero","duro","wole","ye","ye","ranti","pari","de","ko",
    "ka","je","mu","se ise","ko","dun","sare","rin","si","ti","bere","tesiwaju",
    "yi","ran","ko","ra","ta","san","gba","sonu","segun","akoko","odun","ojo",
    "ose","osu","aye","aye","ile-iwe","orile-ede","ebi","akẹkọ","egbe","orile-ede",
    "isoro","owo","apa","ibi","ipo","ami","ijoba","ile-iṣẹ","nomba","eto","ise",
    "eto","ibeere","otito","ile","omi","yara","iya","baba","agbegbe","owo",
    "itan","apa","iru","ori","ise","ore","agbara","wakati","ere","ila","opin",
    "omo egbe","ofin","oko","ilu","agbegbe","oruko","are","egbe","iseju","ero",
    "omo","ara","alaye","eyin","obi","oju","ipele","ofiisi","enu","ilera","eniyan",
    "ona","ogun","egbe oselu","abajade","ayipada","owuro","idi","iwadi","obinrin",
    "okunrin","akoko","afefe","oluko","eko","ese","oselu","ilana","orin","oja",
    "itumo","orile","eto","ife","iku","iriri","ipa","lilo"
}

# ============================================================
# SCORING ENGINE
# ============================================================

def _tokenize(text: str) -> Iterable[str]:
    for m in WORD_RE.finditer(text.lower()):
        yield m.group(0)

def score_text(text: str) -> float:
    """
    Returns a language-agnostic plausibility score.
    Higher = more natural language–like.
    """

    if not text or len(text) < 3:
        return float("-inf")

    tokens = list(_tokenize(text))
    if not tokens:
        return float("-inf")

    counts = Counter(tokens)
    total = sum(counts.values())

    score = 0.0

    for lang, words in LANG_WORDS.items():
        hits = sum(counts[w] for w in counts if w in words)
        if hits:
            lang_score = (hits / total) * WORD_WEIGHT * math.log(len(words))
            score = max(score, lang_score)

    # entropy / repetition penalty
    freq = Counter(text.lower())
    entropy = -sum((c/len(text))*math.log(c/len(text)) for c in freq.values())
    score += entropy * FREQ_WEIGHT

    # weird character penalty
    weird = sum(not ch.isalnum() and ch not in " .,;:'!?-" for ch in text)
    score -= weird * PENALTY_WEIGHT

    return score
