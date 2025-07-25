from flask import Flask, request, jsonify
from flask_cors import CORS
from pythainlp.tokenize import word_tokenize, sent_tokenize
from pythainlp.tag import pos_tag
import re
import os

app = Flask(__name__)
CORS(app)

# 🔹 คำที่ต้องปรับรูปแบบ
question_words = {"ไหม", "มั้ย", "หรือเปล่า", "หรือยัง", "หรือ", "หรอ", "อะไร", "ใช่ไหม", "ไร", "หรอคะ", "คะ",}
adverbs_to_change = {"ด้วยกัน"}
colors = {"สีแดง", "สีส้ม", "สีเหลือง", "สีเขียว", "สีน้ำเงิน",
          "สีฟ้า", "สีม่วง", "สีชมพู", "สีดำ", "สีขาว", "สีเทา", "สีน้ำตาล"}
days = {"วันจันทร์", "วันอังคาร", "วันพุธ", "วันพฤหัสบดี",
        "วันศุกร์", "วันเสาร์", "วันอาทิตย์"}
time_words = {"มะรืน": "พรุ่งนี้ 2", "เมื่อวานซืน": "เมื่อวาน 2"}
eat_words = {"กินน้ำ": "กิน น้ำ", "กินข้าว": "กิน ข้าว"}
words_to_remove = {"ที่", "ก็", "ๆ", "ครับ", "ค่ะ"}

# 🔹 คำพ้องความหมายของ "น้ำ"
_1word = {"คงคา", "คงคาลัย", "ชล", "ชลชาติ", "ชลัมพุ", "ชลาลัย", "โตย", "ทก", "นิระ", "เนียร", "บาน", "บานิโยทก", "บานีโยทก", "ปานะ", "วาริ", "วารี", "สลิล", "สินธุ", "สินธุ์", "สินธู", "อัมพุ", "อาปะ", "อาโป", "อุทก"}
_2word = {"ลำน้ำ", "สายน้ำ", "ท้องน้ำ", "ห้วงน้ำ", "ทะเล", "สมุทร", "กระสินธุ", "กุนที", "คงคา", "คงคาลัย", "คลอง", "แคว", "จทึง", "ฉทึง", "ชทึง", "ชรทึง", "สทิง", "สทึง", "สรทึง", "ชลธาร", "ชลธารก", "ชลธิศ", "ชลธี", "ชลาลัย", "ชลาสินธุ์", "ชโลทร", "ธาร", "ธารา", "นที", "มหรณพ", "มหรรณพ", "มหารณพ", "ยมนา", "รัตนากร", "ลำธาร", "ลำกระโดง", "ลำประโดง", "ลำห้วย", "วหา", "วาหินี", "สริตะ", "สาคร", "สาคเรศ", "สินธุ", "สินธุ์", "สินธู", "อรรณพ", "อุทกธารา", "โอฆะ"}
_3word = {"ขยล", "พระพาย", "มารุต", "วาตะ", "วายุ", "วาโย", "อนิละ"}
_4word = {"กราน", "กูณฑ์", "ชวาล", "ชาลา", "ฑาหะ", "เดช", "เดโช", "เตช", "เตโช", "เพลิง", "ปาวกะ", "ศิขา", "สิขา", "สิขี", "อัคคี", "อัคนี", "อัจจิ"}
_5word = {"พระอาทิตย์", "ตะวัน", "ไถง", "รวิ", "รวี", "รพิ", "รพี", "รำไพ", "สุริยะ", "สุริยา", "สุริยัน", "สุริยน", "สุริยง", "สุรีย์", "สุริยมณฑล", "สูรยมณฑล", "สูรยพิมพ์", "อักกะ", "ทิพากร", "ทิวากร", "ทินกร", "ภากร", "ภาสกร", "อาภากร", "ประภากร", "ภาณุ", "ภาณุมาศ", "รังสิมันตุ์", "รังสิมา", "อังศุธร", "อังศุมาลี", "พันแสง", "จาตุรนต์รัศมี", "สหัสรังสี", "อุษณกร", "อุษณรัศมี", "อุษณรุจี", "อุษณรศมัย"}
_6word = {"พระจันทร์", "เดือน", "แข", "แถง", "บุหลัน", "โสม", "สุมะ", "พิธุ", "วิธู", "มาส", "อินทุ", "จันทรพิมพ์", "จันทรมณฑล", "ศศธร", "ศศพินทุ์", "ศศลักษณ์", "ศศิ", "ศศิน", "ศศี", "ศศิธร", "ศศิมณฑล", "ตโมหร", "มนทกานติ", "สีตลรัศมี", "สิตางศุ์", "โทษากร", "นิศากร", "นิศานาถ", "นิศาบดี", "นิศามณี", "นิศารัตน์", "รัชนีกร", "ปักษธร", "กัษษากร", "ศิวเศขร"}
_7word = {"ชุติ", "ดารา", "ดารกะ", "นักษัตร", "ผกาย"}
_8word = {"ข้างตีน", "อุดร", "อุตดร", "อุตรทิศ"}
_9word = {"ข้างหัวนอน", "ทิกขิณทิศ", "ทักขิณา", "ทักษิณ", "ทักษิณา", "หัวนอน", "อปาจี", "อปาจีน", "อวาจี"}
_10word = {"ข้างออก", "บุรพทิศ", "บุรัตถิมทิศ", "บุริมทิศ", "บูรพาทิศ", "ปราจีน", "ปาจีน"}
_11word = {"ข้างตก", "ประจิม", "ปรัศจิมทิศ", "ปัจฉิมทิศ", "ปัศจิมทิศ", "ทิศอัสดงคต"}
_12word = {"พรรษฤดู", "วรรษา", "วัสสะ", "วัสสานฤดู", "วัสสานะ"}
_13word = {"เดือนเย็น", "ศิศีระ", "ศีตกาล", "หน้าหนาว", "เหมันต์", "เหมันตฤดู"}
_14word = {"กษมา", "ฉมา", "ธรณิน", "ธรณี", "ธรา", "ธราดล", "ธริษตรี", "ธเรษตรี", "ธาตรี", "ธาษตรี", "ปฐวี", "ปฐพี", "ปัถพี", "ปัถวี", "พสุธา", "พสุธาดล", "พสุนธรา", "พสุมดี", "ภพ", "ภูดล", "ภูมิ", "ภูวดล", "มหิ", "มหิดล", "เมทนี", "เมทินี", "โลกธาตุ", "วสุนทรา", "หล้า", "อจลา", "อุรพี"}
_15word = {"ชัฏ", "ดง", "เถื่อน", "ป่าไม้", "พง", "พงพนา", "พงพี", "พงไพร", "พนัส", "พนา", "พนาดร", "พนาดอน", "พนาลัย", "พนาวัน", "พนาเวศ", "พนาสณฑ์", "พนาสัณฑ์", "ไพร", "ไพรวัน", "ไพรสณฑ์", "ไพรสัณฑ์", "ไพรสาณฑ์", "วนา", "วนาดร", "วนาดอน", "วนาลัย", "วนาสณฑ์", "วนาสัณฑ์", "อรัญ", "อรัญญิก"}
_16word = {"คีรี", "นคะ", "บรรพต", "พนม", "ภู", "ภูผา", "ศิขริน", "ศิขรี", "ศิงขร", "ศิงขริน", "ศิงขรี", "ไศล", "สิขร", "สิขรี", "สิงขร"}
_17word = {"นภจร", "ปโยธร", "ปัชชุน", "พลาหก", "เมฆา", "เมฆินทร์", "เมฆี", "วลาหก", "วาริท", "วาริธร", "อัมพุท"}
_18word = {"เผลียง", "พรรษ", "พลาหก", "พิรุณ", "วรรษ", "วัสสะ", "วุฐิ"}
_19word = {"คคนะ", "คคนัมพร", "คคนางค์", "คคนานต์", "ดาราบถ", "ทิฆัมพร", "ไทวะ", "นภดล", "นภมณฑล", "นภา", "นภาลัย", "นักษัตรบถ", "โพยม", "โพยมัน", "โพยมาน", "ลางงิด", "วยัมหะ", "เวหน", "เวหา", "เวหาส", "เวหายส", "สรวง", "สันรวง", "สุรบถ", "หาว", "อัมพร", "อากาศ"}
_20word = {"กระยาหงัน", "ไกพัล", "ไกวัล", "ไตรทิพย์", "ไตรทศาลัย", "เทวโลก", "ไทวะ", "เมืองฟ้า", "เมืองแมน", "เมืองอมร", "ลางงิด", "วยัมหะ", "สรวง", "สันรวง", "สัค", "สัคคะ", "สุขาวดี", "สุคติ", "สุรบถ", "สุรโลก", "สุราลัย"}
_21word = {"ทุคติ", "นรกานต์", "ยมโลก"}
_22word = {"พระสัมมาสัมพุทธเจ้า", "พระสัพพัญญู", "พระโลกนาถ", "พระสุคต", "พระผู้มีพระภาคเจ้า", "ชินศรี", "พระสมณโคดม", "พระศากยมุนี", "พระธรรมราช", "พระชินสีห์", "พระทศญาณ", "มารชิต", "โลกชิต", "พระทศพลญาณ", "พระตถาคต", "พระชินวร"}
_23word = {"เทพ", "เทวินทร์", "อมร", "สุรารักษ์", "แมน", "เทว", "เทวัญ", "นิรชรา", "เทวา", "ไตรทศ", "ปรวาณ", "สุร"}
_24word = {"เทพธิดา", "เทวี", "นางสวรรค์", "รัมภา", "อัจฉรา", "อัปสร", "สุรางคนา", "นิรชรา"}
_25word = {"กมลาสน์", "กัมลาศ", "ครรไลหงส์", "จตุรพักตร์", "จัตุรพักตร์", "ธาดา", "ปรเมษฐ์", "ประชานาถ", "ปิตามหะ", "พรหมธาดา", "พรหมา", "พรหมินทร์", "พรหเมนทร์", "พรหเมศวร", "หงสรถ"}
_26word = {"ศิวะ", "ศุลี", "มหาเทพ", "สยมภู", "ภูเตศวร", "จันทรเศขร", "ศังกร"}
_27word = {"วิษณุ", "จักรปาณี", "จักรี", "ธราธร", "ธราธาร"}
_28word = {"โกสีย์", "โกสินทร์", "เทพบดี", "พันตา", "พันเนตร", "เพชรปาณี", "เพชรายุธ", "มฆวัน", "มหินท์", "มเหนทร์", "มัฆวา", "มัฆวาน", "วชิรหัตถ์", "วชิราวุธ", "วัชรปาณี", "วัชรินทร์", "วัชรี", "วัชเรนทร์", "วาสพ", "ศักรินทร์", "ศักเรนทร์", "สวรรคบดี", "สหัสนัยน์", "สหัสเนตร", "สักกะ", "สุชัมบดี", "สุรบดี", "สุรินทร์", "สุเรนทร์", "อมรบดี", "อมรราช", "อมรินทร์", "อมเรนทร์", "อมเรศ", "อมเรศวร"}
_29word = {"กาศยปิ", "เวนไตย", "สุบรรณ", "ครุตมาน", "สิตามัน", "รักตปักษ์", "เศวตโรหิต", "สุวรรณกาย", "คคเนศวร", "ขเคศวร", "นาคนาศนะ", "สุเรนทรชิต", "นาคานดก", "นาคานตกะ", "ปันนคนาสน์", "วิษณุรถ"}
_30word = {"ยักษา", "ยักษี", "ยักษิณี", "ยักข์", "ยักขินี", "อสูร", "อสุรา", "อสุรี", "อสุเรศ", "กุมภัณฑ์", "แทตย์", "ทานพ", "รากษส", "ราพณ์", "ราพณาสูร"}
_31word = {"มุนี", "ฤษี", "ฤๅษี", "ดาบส", "นักพรต", "นักสิทธิ์", "นิครนถ์", "บรรพชิต", "บาทหลวง", "ปริพาชก", "ภิกขุ", "ภิกษุ", "โยคี", "หลวงจีน"}
_32word = {"ธีระ", "เธียร", "บัณฑิต", "ปราชญ์", "ปัญญาชน", "พหูสูต", "เมธาวี", "เมธี", "วิญญู"}
_33word = {"กูรู", "เซียน", "ผู้รู้", "ผู้สันทัดกรณี"}
_34word = {"เก่ง", "เก๋า", "โกวิท", "คร่ำหวอด", "จัดเจน", "ชาญ", "ช่ำชอง", "ชำนิ", "ชำนิชำนาญ", "ชำนาญ", "ถนัด", "สันทัด"}
_35word = {"โกวิท", "โกศล", "คมคาย", "จินดาหรา", "ฉลาดเฉลียว", "เฉียบแหลม", "ชาญฉลาด", "ทันคน", "ธีระ", "เธียร", "ประทักษ์", "ประพิณ", "ประวีณ", "ปราดเปรื่อง", "ปวีณ", "พยัต", "พฤทธ์", "พิทูร", "วิจักขณ์", "วิจักษณ์", "วิทูร", "วิสารทะ", "หลักแหลม", "หัวดี", "หัวไว", "หัวแหลม", "อัจฉริยะ"}
_36word = {"กำเลา", "กินแกลบกินรำ", "กินหญ้า", "ขี้เท่อ", "เขลา", "งั่ง", "งี่เง่า", "โง่เขลา", "โง่งม", "โง่เง่า", "โง่เง่าเต่าตุ่น", "เฉาโฉด", "โฉด", "โฉดเฉา", "ซื่อบื้อ", "เซ่อ", "เซอะ", "เซอะซะ", "ทึบ", "ทึ่ม", "ปัญญาทึบ", "ปัญญาอ่อน", "ปัญญาอับ", "มนท์", "โมมูห์", "โมมูหะ", "สมองกลวง", "สมองขี้เลื่อย", "สมองทึบ", "หัวขี้เลื่อย", "หัวทึบ"}
_37word = {"ขี้ตืด", "ขี้หวง", "งก", "ตระหนี่", "มัจฉระ", "มัตสระ"}
_38word = {"กระเบียดกระเสียร", "กระเหม็ดกระแหม่", "เขม็ดแขม่", "จำกัดจำเขี่ย", "มัธยัสถ์", "อดออม"}
_39word = {"ใจเติบ", "ใจใหญ่ใจโต", "ฟุ้งเฟ้อ", "มือเติบ", "สิ้นเปลือง", "สุรุ่ยสุร่าย", "หน้าใหญ่ใจโต", "อีฉุยอีแฉก", "อีลุ่ยฉุยแฉก", "อีหลุยฉุยแฉก"}
_40word = {"เอื้อเฟื้อเผื่อแผ่", "ใจกว้าง", "ใจดี", "ใจบุญ", "ใจป้ำ", "มีน้ำใจ", "อารี", "อารีอารอบ", "โอบอ้อมอารี"}
_41word = {"ช้าง", "กุญชร", "กรี", "กริน", "กริณี", "กรินี", "กิริณี", "กิรินี", "กรินทร์", "กเรนทร", "กเรนทร์", "กเรณุ", "กเรณุกา", "คช", "คชสาร", "คชา", "คชาชาติ", "คชาธาร", "คชินทร์", "คเชนทร์", "เจ่ง", "ดำรี", "ดำไร", "ดมไร", "ทันติน", "ทันตี", "ทนดี", "ทวิป", "นรการ", "นาค", "นาคี", "นาคินทร์", "นาเคนทร์", "นาเคศ", "นาเคศวร", "พลาย", "พัง", "พารณ", "พารณะ", "พาฬ", "มาตงค์", "มาตังคะ", "สาง", "สาร", "สินธุระ", "สีดอ", "หัตถี", "หัตถินี", "หัสดี", "หัสดิน", "ไอยรา"}
_42word = {"ม้า", "ดุรงค์", "ตุรงค์", "พาชี", "มโนมัย", "สินธพ", "แสะ", "หัย", "อัศวะ", "อัสสะ", "อัสดร", "อาชา"}
_43word = {"วัว", "โค", "คาวี", "งัว", "พฤษภ", "วฤษภ"}
_44word = {"ควาย", "กาสร", "กระบือ", "มหิงส์", "มหิงสา", "มหิษ", "ลุลาย"}
_45word = {"สิงโต", "เกสรี", "ไกรศร", "ไกรศรี", "ไกรสร", "ไกรสรี", "เจ้าป่า", "พาฬ", "ราชสีห์", "สิงห์", "สิงหราช", "สีห์", "สีหราช"}
_46word = {"เสือ", "ขลา", "ขาล", "ตะโก", "ทวีปี", "พยัคฆ์", "พยัคฆา", "พยัคฆิน", "พยัคฆี", "พาฬ", "ศารทูล", "อชินี"}
_47word = {"ลิง", "กบิล", "กบี่", "กบินทร์", "กเบนทร์", "กระบี่", "กปิ", "จ๋อ", "พลีมุข", "วอก", "วานร", "พานร", "วานรินทร์", "พานรินทร์", "พานเรศ", "มักฏะ", "สวา", "ชรโมล"}
_48word = {"นก", "สกุณ", "สกุณา", "สกุณี", "สกุนต์", "ศกุน", "ศกุนต์", "ศกุนิ", "ปักษิน", "ปักษี", "ปักษา", "บุหรง", "วิหค", "วิหงค์", "เวหังค์", "สุโนก", "สรุโนก", "ทวิช", "ทิชากร", "ทวิชาชาติ"}
_49word = {"นกยูง", "มยุระ", "มยุรี", "มยุรา", "มยุเรศ", "เมารี", "โมรี"}
_50word = {"ปลา", "มัจฉา", "มัสยา", "มัจฉาชาติ", "มีน", "ตรี", "ตฤๅ", "ปุถุโลม", "ชลาศัย", "อัมพุช", "วาริช", "วารีช", "วารีชาติ", "ชลจร", "นีรจร"}
_51word = {"งู", "โฆรวิส", "เงี้ยว", "ทีฆชาติ", "เทียรฆชาติ", "นาค", "นาคา", "นาคี", "ผณิ", "ผณิน", "พาฬ", "ภุชคะ", "ภุชงค์", "ภุชงคมะ", "โภคิน", "โภคี", "วิษธร", "สรีสฤบ", "สัปปะ", "อสรพิษ", "อหิ", "อาศิรพิษ", "อาศิรวิษ", "อาศีรพิษ", "อาศีรวิษ", "อุรคะ"}
_52word = {"หมู", "จรุก", "วราห์", "วราหะ", "ศูกร", "สุกร"}
_53word = {"หมา", "จอ", "สุนัข", "ศวา", "ศวาน", "สุวาน", "โสณะ"}
_54word = {"แมว", "ชมา", "พิฬาร", "มัชชาระ", "วิฬาร", "วิฬาร์", "เหมียว"}
_55word = {"จระเข้", "กุมภา", "กุมภิล", "กุมภีล์", "ตะเข้", "นักกะ", "นักระ"}
_56word = {"เต่า", "กริว", "กัศยป", "กูรมะ", "จริว", "จิตรจุล", "ตริว", "อันโด๊ก"}
_57word = {"ตะพาบ", "กราว", "กริว", "จมูกหลอด", "จราว", "จริว", "ตริว", "ตะพาบน้ำ", "ปลาฝา", "อันโด๊ก"}
_58word = {"ดอกไม้", "โกสุม", "กุสุม", "กุสุมา", "กุสุมาลย์", "บุษบา", "บุษบง", "บุษบัน", "บุปผา", "บุปผชาติ", "บุหงา", "ผกา", "มาลย์", "มาลา", "มาลี", "สุมาลี"}
_59word = {"บัว", "กมล", "กมลาศ", "กมเลศ", "กระมล", "โกมล", "จงกล", "จงกลนี", "ตาราไต", "นิลุบล", "นิโลตบล", "นีรช", "นีรชะ", "บงกช", "บุณฑริก", "บุษกร", "ปทุม", "ปทุมา", "ปัทม์", "ปัทมา", "สัตตบงกช", "สัตตบรรณ", "สโรชะ", "สาโรช", "วาริช", "วารีช", "อัมพุช", "อุบล"}
_60word = {"หญ้า", "เกลียง", "ตฤณ", "ตฤณชาติ", "ติณ", "ติณชาติ", "ยาวัส", "หริต"}
_61word = {"ต้นไม้", "พฤกษ์", "รุกข์", "ตรุ", "เฌอ", "ทุม", "ปาทป", "บาทบ"}
_62word = {"ราชพฤกษ์", "คูน", "ลมแล้ง"}
_63word = {"กัลปพฤกษ์", "กาลพฤกษ์", "เปลือกขม"}
_64word = {"จั๋งไทย", "จั๋งใต้"}
_65word = {"ขนุนปาน", "ขนุนป่า"}
_66word = {"เมือง", "ธานิน", "ธานินทร์", "ธานี", "นคร", "นครินทร์", "นคเรศ", "บุระ", "บุรินทร์", "บุรี", "ปุระ", "พารา"}
_67word = {"เมืองหลวง", "กรุง", "นครหลวง", "พระนคร", "ราชธานี"}
_68word = {"กษัตริย์", "ขัตติยะ", "บดี", "บดินทร์", "บพิตร", "นฤบดี", "ภูวไนย", "ภูมินทร์", "นฤบาล", "นฤเบศร์", "นฤบดี", "นฤบดินทร์", "บพิตร", "พระเจ้าอยู่หัว", "พระเจ้าแผ่นดิน", "ในหลวง", "พ่ออยู่หัว", "เหนือหัว", "ภูบดี", "นรินทร์", "นเรนทร์", "นโรดม", "นราธิป", "ธเรศ", "จักรพรรดิ์", "ราชัน", "ราชา", "ราชาธิราช", "ราช", "ราเชนทร์", "อดิศรภูวนาถ", "ภูมิบาล", "ภูบาล", "ภูธเรศ", "ภูนาถ", "ภูนายก", "ภูเนตุ", "ภูบดินทร์", "ภูเบศ", "ธราธิบดี", "ธราธิป", "ธรณีศวร", "ธรณิศ", "ธรนิศร", "ธรณิศวร์", "นริศ", "ธรณินทร์", "อธิราช", "อธิป", "จักรี"}
_69word = {"หมอ", "จีนแส", "ซินแส", "แพทย์", "ภิษัช", "ภิสัก", "เวช", "ไวทย์"}
_70word = {"โสเภณี", "กะหรี่", "คณิกา", "นครโสภิณี", "นครโสเภณี", "นางกลางเมือง", "นางโลม", "แพศยา", "เวศยา", "เวสิ", "เวสิยา", "โสภิณี", "หญิงขายบริการ", "หญิงงามเมือง", "หญิงนครโสภิณี", "หญิงนครโสเภณี", "หญิงหากิน", "อีตัว"}
_71word = {"คน", "นร", "นรชาติ", "นรา", "นรากร", "บุคคล", "ผู้", "มนุษย์", "มรรตยะ", "มรรตัย", "มัจจะ", "มัตตัย", "มัตยะ", "มานพ"}
_72word = {"ประชาชน", "ชาวบ้าน", "ชาวเมือง", "ประชาชี", "ประชาราษฎร์", "ปั่ว", "ฝุ่นเมือง", "พลเมือง", "พสก", "พสกนิกร", "ไพร่", "ไพร่ฟ้า", "มหาชน", "ราษฎร", "เลก"}
_73word = {"ศัตรู", "ข้าศึก", "ดัสกร", "ปฏิปักษ์", "ปรปักษ์", "ปัจจามิตร", "ปัจนึก", "ไพรี", "เวรี", "ริปู", "อริ"}
_74word = {"ผู้หญิง", "กระลาพิม", "กระลาศรี", "กัญญา", "กันย์", "กันยา", "กัลยา", "กัลยาณี", "กานดา", "กามินี", "แก้วตา", "จอมขวัญ", "จอมใจ", "ฉัยยา", "โฉมตรู", "ไฉยา", "ชารี", "ดรุณี", "ดวงสมร", "ถี", "ทรามเชย", "ทรามวัย", "ทรามสงวน", "ทรามสวาท", "นงคราญ", "นงพะงา", "นงพาล", "นงพุธ", "นงโพธ", "นงเยาว์", "นงราม", "นงลักษณ์", "นรี", "นารี", "นาเรศ", "นิรมล", "บังอร", "พธู", "พนิดา", "พุ่มพวง", "ภีรุ", "มาณวิกา", "มาตุคาม", "มารศรี", "ยุพดี", "ยุพยง", "ยุพเยาว์", "ยุพเรศ", "ยุพา", "ยุพาน", "ยุพาพาล", "ยุพาพิน", "ยุพิน", "ยุวดี", "เยาวพา", "เยาวมาลย์", "เยาวเรศ", "เยาวลักษณ์", "รมณี", "ร้อยชั่ง", "ลลนา", "วธู", "วนิดา", "วรดนู", "สตรี", "สมร", "สะคราญ", "สายสมร", "สุดา", "อนงค์", "อร", "อรทัย", "อรนุช", "อังคณา", "อิตถี", "อิสตรี", "อิสัตรี"}
_75word = {"เด็ก", "พาล", "ทารก", "ดรุณ", "กุมาร", "ศิศุ"}
_76word = {"พ่อ", "ชนก", "เตี่ย", "บิดร", "บิดา", "บิตุรงค์", "บิตุเรศ", "ป๋า", "ปาปอหยีสังฆาตา", "ปิตุ", "สังคาตา"}
_77word = {"แม่", "ชนนี", "ชเนตตี", "นนทลี", "มาดา", "มาตฤ", "มาตา", "มาตุ", "มาตุรงค์", "มาตุเรศ", "มารดร", "มารดา", "เม", "อัมพา"}
_78word = {"ปู่", "ก๋ง", "ปิตามหะ", "อัยกะ", "อัยกา"}
_79word = {"ย่า", "อัยกี", "อัยยิกา"}
_80word = {"ตา", "ก๋ง", "ขรัวตา", "มาตามหะ", "อัยกะ", "อัยกา"}
_81word = {"ยาย", "ขรัวยาย", "มาตามหา", "อัยกี", "อัยยิกา"}
_82word = {"ภรรยา", "เมีย", "ภริยา", "ฆรณี", "ปัตนี", "สนม", "ชายา", "ชาเยนทร์", "ชาเยศ", "มเหสี"}
_83word = {"สามี", "ผัว", "สวามี", "ภัสดา", "ภรรดร", "ภรรดา"}
_84word = {"ลูก", "บุตร", "กูน", "ดนุช", "เอารส"}
_85word = {"ลูกชาย", "บุตร", "โอรส", "ดนยะ", "ดนัย"}
_86word = {"ลูกสาว", "บุตรี", "ธิดา", "สุดา", "ดนยา"}
_87word = {"น้องชาย", "กนิษฐภาดา", "อนุชา"}
_88word = {"เพื่อน", "เกลอ", "คนสนิท", "คู่ซี้", "คู่หู", "มิตร", "วยัสย์", "สขะ", "สขา", "สขิ", "สหาย", "เสี่ยว"}
_89word = {"ใจ", "กมล", "กระมล", "มโน", "มน", "แด", "หทัย", "หฤทัย", "ฤทัย", "ฤดี", "จิต", "ดวงใจ", "หัวใจ"}
_90word = {"หัว", "กบาล", "กระบาล", "พระเจ้า", "มัตถกะ", "มัสดก", "มุทธา", "มุรธา", "มูรธา", "ศิระ", "ศิรามพุช", "ศีรษะ", "เศียร", "สิระ", "สิโรดม", "สิโรตม์", "สีสะ"}
_91word = {"ผม", "เกศ", "เกศธาตุ", "เกศา", "เกศี", "เกส", "เกสา", "เกสี", "ขนหัว", "เผ้า", "ศก", "สก", "เส้นพระเจ้า"}
_92word = {"เท้า", "ตีน", "บท", "บทบงกช", "บทมาลย์", "บทเรศ", "บทวเรศ", "บทศรี", "บทามพุช", "บัวบาท", "บาท", "บาทบงกช", "บาทา"}
_93word = {"ตา", "จักขุ", "จักษุ", "ดวงตา", "นยนะ", "นยนา", "นัยน์", "นัยน์ตา", "นัยน์เนตร", "นัยนา", "เนตร", "ลูกตา"}
_94word = {"คิ้ว", "ขนง", "โขนง", "เจิม", "ภมุ", "ภมุกะ", "ภมุกา", "ภรู", "ภรูมณฑล"}
_95word = {"ปาก", "มุลุต", "ลปนะ", "วทนะ", "วัทน์", "อานน", "โอฐ", "โอษฐ์"}
_96word = {"ฟัน", "ทนต์", "ทันต์", "ฟาง", "รท", "รทนะ", "กราม", "เขี้ยว", "ทาฐะ", "ทาฒะ"}
_97word = {"ลิ้น", "ชิวหา", "มลิ้น", "รสนา", "อันด๊าก"}
_98word = {"ทองคำ", "กนก", "กัมพู", "กาญจน์", "กาญจนา", "กำภู", "คำ", "จามีกร", "จารุ", "ชมพูนท", "ชมพูนุท", "ชัมพูนท", "ชามพูนท", "ชาตรูป", "ตปนียะ", "นพคุณ", "มาศ", "สิงคี", "สุพรรณ", "สุวรรณ", "หาดก", "หาตกะ", "เหม", "อุไร"}
_99word = {"เงิน", "รชตะ", "รัชดา", "รัชฎา", "ปรัก", "หิรัญ", "หิรัณย์"}
_100word = {"เพชร", "มณิ", "มณี", "พัชร", "พชระ", "วิเชียร", "วชิร", "วชิระ", "วัชระ"}
_101word = {"เรือ", "ดารณี", "ตูก", "ตรณี", "นาเวศ", "นาวา", "นาวี", "เนา", "เภตรา"}
_102word = {"ธง", "เกตุ", "ตุง", "ธชะ", "ธวัช", "ธัช", "ธุช", "บรรดาก", "ประดาก"}
_103word = {"หิน", "กรวด", "โขด", "ถมอ", "ปราษาณ", "ปาษาณ", "ปาสาณ", "ผลา", "ศิลา", "สมอ", "สิลา", "เสลา"}
_104word = {"ขยะ", "กระหยะ", "กาก", "กากขยาก", "กุมฝอย", "ของเสีย", "คุมฝอย", "เดน", "มูลฝอย", "สังการ", "สิ่งปฏิกูล", "หยากเยื่อ"}
_105word = {"แก่", "งอม", "ชรา", "เฒ่า", "มีอายุ", "สูงวัย", "สูงอายุ", "อาวุโส", "หง่อม"}
_106word = {"กิน", "เขมือบ", "เจี๊ยะ", "ซัด", "โซ้ย", "แดก", "บริโภค", "ฟาด", "โภค", "ยัด", "รับประทาน", "สวาปาม", "เสพ", "เสวย", "หม่ำ", "แอ้ม"}
_107word = {"นอน", "งีบ", "จำวัด", "บรรทม", "ประทม", "ผทม", "ไสยาสน์", "เอนกาย", "เอนตัว", "เอนหลัง"}
_108word = {"ป่วย", "เจ็บ", "เจ็บไข้", "เจ็บป่วย", "ประชวร", "ไม่สบาย", "อาพาธ"}
_109word = {"ตาย", "กระทำกาลกิริยา", "กระทำกาละ", "กลับบ้านเก่า", "ขาดใจ", "ชีวาลัย", "ชีวิตักษัย", "ซี้", "ดับ", "ดับขันธ์", "ดับชีพ", "ตักษัย", "ถึงแก่กรรม", "ถึงแก่พิราลัย", "ถึงแก่มรณกรรม", "ถึงแก่อนิจกรรม", "ถึงแก่อสัญกรรม", "ถึงชีพิตักษัย", "ถึงซึ่งกาลกิริยา", "ทิวงคต", "ทำกาลกิริยา", "ทำกาละ", "เท่งทึง", "นิคาลัย", "ปรินิพพาน", "ไปค้าถ่าน", "พิราลัย", "มรณภาพ", "มรณะ", "มลาย", "ม้วย", "ม้วยมอด", "ม่องเท่ง", "มอดม้วย", "ล่วงลับ", "ละสังขาร", "ลาโลก", "วางวาย", "วายชนม์", "วายชีวิต", "วายปราณ", "วายวาง", "วายสังขาร", "สวรรคต", "สิ้น", "สิ้นกรรม", "สิ้นกรรมสิ้นเวร", "สิ้นใจ", "สิ้นชีพ", "สิ้นชีพตักษัย", "สิ้นชีวิต", "สิ้นชื่อ", "สิ้นบุญ", "สิ้นพระชนม์", "สิ้นลม", "สิ้นลมปราณ", "สิ้นเวร", "สิ้นเวรสิ้นกรรม", "สิ้นสังขาร", "สิ้นอายุขัย", "เสีย", "เสียชีวิต", "หมดกรรม", "หมดกรรมหมดเวร", "หมดบุญ", "หมดลม", "หมดเวร", "หมดเวรหมดกรรม", "อาสัญ"}
_110word = {"ฆ่า", "เข่นฆ่า", "คร่าชีวิต", "ฆ่าแกง", "ฆ่าฟัน", "เด็ดหัว", "ประหัต", "ประหัตประหาร", "ประหาร", "ปลิดชีพ", "ผลง", "พิฆาต", "มล้าง", "วัชฌ์", "วิฆาต", "สังหาร", "หตะ", "อภิฆาต", "เอาชีวิต"}
_111word = {"ทำลาย", "กรุน", "กวาดล้าง", "กำจัด", "ขจัด", "ถอนต้นก่นราก", "ถอนยวง", "ถอนรากถอนโคน", "พร่า", "พัง", "ผลาญ", "มล้าง", "ม้าง", "ล้างผลาญ", "หตะ", "อภิฆาต"}
_112word = {"สงคราม", "จำบัง", "ฉุป", "ณรงค์", "ยุทธ์", "ยุทธนา", "รณรงค์", "ศึก", "สมร"}
_113word = {"สนามรบ", "ยุทธภูมิ", "รงค์", "รณเกษตร", "รณภู", "รณภูมิ", "รณรงค์", "รณสถาน", "สมรภูมิ", "อชิระ"}
_114word = {"พยายาม", "ทุ่มเท", "บากบั่น", "พากเพียร", "เพียร", "มานะ", "มุ", "มุมานะ", "อุตส่าห์", "อุตสาหะ"}
_115word = {"สร้าง", "ก่อ", "ทำ", "นฤมิต", "นิมิต", "นิรมิต", "เนรมิต", "บพิธ", "ประดิษฐ์", "ผลิต", "รังสรรค์", "รังสฤษฏ์", "สถาบก", "สรรค์", "สรรค์สร้าง", "สร้างสรรค์"}
_116word = {"เกิด", "กำเนิด", "ชาตะ", "ตกฟาก", "ถือกำเนิด", "ทรงพระราชสมภพ", "ประสูติ", "เสวยพระชาติ", "สูนะ", "อุบัติ"}
_117word = {"ไหว้", "กราบ", "คารวะ", "คำนับ", "ถวายบังคม", "นอบน้อม", "บูชา", "ประณต", "ประณม", "วันทา", "อัญชลี", "อัญชุลี", "ชุลี"}
_118word = {"ดู", "จ้อง", "ชม", "ชระเมียง", "ชะเง้อ", "ชายตา", "ชำเลือง", "ทอดตา", "ทอดพระเนตร", "เพ่ง", "มอง", "เมิล", "เมียง", "ยล", "แยงยล", "เล็ง", "แล"}
_119word = {"เดิน", "กราย", "คลาไคล", "ไคลคลา", "จรลี", "เดินเหิน", "เตร่", "ทอดน่อง", "บทจร", "ผเดิน", "ยาตร", "ยาตรา", "ยุรยาตร", "เยื้องย่าง"}
_120word = {"ไป", "ครรไล", "คระไล", "ไคล", "จร", "เต้า"}
_121word = {"แต่งงาน", "วิวาห์", "อาวาหะ", "สมพงศ์", "สมรส", "อภิเษกสมรส"}
_122word = {"เศร้า", "กำสรด", "กำสรวล", "คร่ำครวญ", "ชอกช้ำ", "ช้ำใจ", "ช้ำชอก", "มลาน", "ร้องไห้", "ระทด", "ระทม", "รันทด", "เศร้าโศก", "เศร้าหมอง", "โศก", "โศกศัลย์", "โศกเศร้า", "โศกสลด", "โศกา", "โศกี", "สลด"}
_123word = {"โกรธ", "กริ้ว", "เกรี้ยวโกรธ", "โกรธเกรี้ยว", "โกรธขึ้ง", "โกรธา", "ขึ้งโกรธ", "ขึ้งเคียด", "เดือดดาล", "พิโรธ", "พื้นเสีย", "โมโห"}
_124word = {"สวยงาม", "โกมล", "งดงาม", "งาม", "แฉล้ม", "ไฉไล", "ตระการ", "ประไพ", "พริ้ง", "พริ้งพราย", "พริ้งเพรา", "พริ้งเพริศ", "พะงา", "พิจิตร", "ไพจิตร", "มล่าวเมลา", "รงรอง", "รจิต", "รังรอง", "รังเรข", "รุจิเรข", "ลออ", "วิจิตร", "วิลาวัณย์", "วิไล", "สวย", "สะคราญ", "สิงคลิ้ง", "สุทรรศน์", "สุทัศน์", "เสาวภา", "เสาวลักษณ์", "โสภณ", "โสภา", "โสภี", "หาริ", "อภิราม", "อะเคื้อ", "อันแถ้ง", "อำไพ"}
_125word = {"รุ่งเรือง", "จรัส", "จำรัส", "ชวลิต", "ชัชวาล", "โชติช่วง", "รุ่งโรจน์", "รุจิ", "รุจี"}
_126word = {"เลิศ", "เจ๋ง", "บวร", "ประเสริฐ", "ล้ำเลิศ", "วิศิษฏ์", "วิเศษ", "ยอด", "ยอดเยี่ยม"}
_127word = {"ขี้เหร่", "ขี้ริ้ว", "น่าเกลียด", "น่ารังเกียจ", "รูปชั่ว", "อัปลักษณ์"}
_128word = {"เลว", "จังไร", "จัญไร", "ชั่ว", "ชั่วช้า", "ชั่วร้าย", "ต่ำช้า", "ทราม", "แย่", "ระยำ", "ระยำตำบอน", "เลวทราม", "สาธารณ์", "สามานย์", "อัปมงคล", "อัปรีย์"}
_129word = {"อาหาร", "กับข้าว", "ของกิน", "เสบียง", "จังหัน", "นิตยภัต", "บิณฑบาต", "ผลาหาร", "ภักขะ", "ภักษา", "ภักษาหาร", "ภัตตาหาร", "โภชนียะ", "ขาทนียะ", "ลฆุโภชน์", "สมพล", "สัมพล"}
_130word = {"เยี่ยว", "กะชัง", "ฉี่", "บังคนเบา", "ปัสสาวะ", "มุตตะ", "มูตร", "เยี่ยว"}
_131word = {"เยี่ยว", "เก็บดอกไม้", "ฉี่", "ชิ้งฉ่อง", "เด็ดดอกไม้", "ถ่ายเบา", "ถ่ายปัสสาวะ", "ปลดทุกข์", "ปัสสาวะ", "ยิงกระต่าย", "ลงพระบังคนเบา"}
_132word = {"ขี้", "กรีษ", "กรีส", "คูถ", "บังคนหนัก", "มูล", "วัจจะ", "อาจม", "อึ", "อุจจาระ", "อุนจิ", "พรรดึก", "มลโค"}
_133word = {"ขี้", "ถ่าย", "ถ่ายท้อง", "ถ่ายทุกข์", "ถ่ายหนัก", "ถ่ายอุจจาระ", "ปลดทุกข์", "ไปทุ่ง", "ลงพระบังคนหนัก", "อึ", "อุจจาระ"}
_134word = {"คำพูด", "ถ้อย", "พจน์", "พจนา", "พากย์", "พาท", "วจนะ", "วัจน์", "วจี", "วทนะ", "วัทน์", "วาจา", "วาท", "วาทะ"}
_135word = {"พูด", "กระพอก", "กล่าว", "คุย", "จรรจา", "จา", "จำนรรจ์", "จำนรรจา", "เจรจา", "ดำรัส", "ตรัส", "บอก", "ประภาษ", "ปราศรัย", "เปรย", "ฝอย", "พรอก", "พร้อง", "ภณะ", "ภาษ", "รับสั่ง", "เล่า", "วทะ", "ว่า", "เว้า", "สนทนา", "อื้น", "เอิ้น", "เอื้อน", "เอ่ย", "เอื้อนเอ่ย"}
_136word = {"ทวี", "คูณ", "เพิ่มพูน", "พอกพูน"}
_137word = {"สี่", "สองคู่", "จตุ"}
_138word = {"ยี่สิบ", "ซาว", "พิศ", "เพส", "วีสะ"}
_139word = {"กกต.", "คณะกรรมการการเลือกตั้ง"}
_140word = {"มหาวิทยาลัยขอนแก่น", "มข.", "มอดินแดง", "มหาลัยขอนแก่น", "ม.ขอนแก่น"}
_141word = {"จุฬาลงกรณ์มหาวิทยาลัย", "จุฬา", "จุฬาฯ", "จุฬาลงกรณมหาวิทยาลัย"}
_142word = {"มกราคม", "ม.ค.", "มกรา"}
_143word = {"กุมภาพันธ์", "ก.พ.", "กุมภา"}
_144word = {"มีนาคม", "มี.ค.", "มีนา"}
_145word = {"เมษายน", "เม.ย.", "เมษา"}
_146word = {"พฤษภาคม", "พ.ค.", "พฤษภา"}
_147word = {"มิถุนายน", "มิ.ย.", "มิถุนา"}
_148word = {"กรกฎาคม", "ก.ค.", "กรกฎา"}
_149word = {"สิงหาคม", "ส.ค.", "สิงหา"}
_150word = {"กันยายน", "ก.ย.", "กันยา"}
_151word = {"ตุลาคม", "ต.ค.", "ตุลา"}
_152word = {"พฤศจิกายน", "พ.ย.", "พฤศจิกา"}
_153word = {"ธันวาคม", "ธ.ค.", "ธันวา"}
_154word = {"เวลา", "กาล", "คราว", "ครั้ง", "ครู่", "เพลา", "ยาม", "หน"}
_155word = {"กลางคืน", "รัชนี", "รัตติ", "รัตติกาล", "ราตรี", "นิศา", "นิศากาล"}
_156word = {"กลางวัน", "ทิวากร", "ทิวากาล"}
_157word = {"วัน", "ทิวา", "ทิน", "ทิพา", "ทิวะ"}
_158word = {"เลือด", "โลหิต", "รุธิระ", "รุเธียร", "โรหิต"}
_159word = {"แดง", "ชาด", "ประวาลวรรณ", "มันปู", "รุธิระ", "รุเธียร", "โรหิต", "กษาย", "มณีราค", "โศณะ", "หง"}
_160word = {"ขาว", "ชุณห", "ชุษณะ", "ซีด", "ด่อน", "เผือก", "นวล", "พบู", "พิศุทธ์", "วิศุทธ์", "วิศุทธิ์", "วิสุทธ์", "วิสุทธิ์", "ศุกล", "ศุภร", "เศวต", "เศวตร", "สกาว", "สอ", "อรชุน"}
_161word = {"ดำ", "กัณห", "กาฬ", "จะกรุน", "จะกรูน", "ทะมึน", "นิล", "ศยาม", "ศยามล", "สามะ", "สามล", "อสิตะ"}
_162word = {"ใหญ่", "กว้าง", "มหันต์", "มหา", "มหึมา", "พิบูล", "ไพศาล", "มโหฬาร"}
_163word = {"อ้วน", "อ้วนจ้ำม่ำ", "อวบอ้วน", "อ้วนท้วน", "อ้วนพี", "จ้ำม่ำ", "ท้วม", "เจ้าเนื้อ", "อวบ", "อวบอั๋น", "อวบอัด"}
_164word = {"ผอม", "ซูบ", "ผอมบาง", "ซูบผอม", "ผ่ายผอม", "ผอมโซ", "ซูบซีด"}
_165word = {"อร่อย", "กระป่ำ", "กระเอบ", "แซบ", "ถูกปาก", "นัว", "รสดี", "รสเด็ด", "เลิศรส", "สาทุ", "เสาวรส", "เอมโอช", "เอร็ดอร่อย", "โอชะ", "โอชา"}
_166word = {"เสือก", "จุ้น", "จุ้นจ้าน", "เจ๋อ", "เจ๋อเจ๊อะ", "ละลาบละล้วง", "สอดรู้", "สอดรู้สอดเห็น", "สะเหล่อ", "สะเออะ", "สาระแน", "สู่รู้", "เสนอหน้า", "เสือกกะโหลก", "แส่", "ยื่นจมูก"}
_167word = {"ไม่", "มิ", "บราง", "หาไม่", "บมิ", "บ่", "ไป่", "ห่อน"}



# 🔹 Map คำพ้องให้เป็นคำหลัก
synonyms_map = {
    word: synonym
    for word_set, synonym in [
        (_1word, "น้ำ"),
        (_2word, "แม่น้ำ"),
        (_3word, "ลม"),
        (_4word, "ไฟ"),
        (_5word, "ดวงอาทิตย์"),
        (_6word, "ดวงจันทร์"),
        (_7word, "ดวงดาว"),
        (_8word, "เหนือ"),
        (_9word, "ใต้"),
        (_10word, "ตะวันออก"),
        (_11word, "ตะวันตก"),
        (_12word, "ฤดูฝน"),
        (_13word, "ฤดูหนาว"),
        (_14word, "แผ่นดิน"),
        (_15word, "ป่า"),
        (_16word, "ภูเขา"),
        (_17word, "เมฆ"),
        (_18word, "ฝน"),
        (_19word, "ท้องฟ้า"),
        (_20word, "สวรรค์"),
        (_21word, "นรก"),
        (_22word, "พระพุทธเจ้า"),
        (_23word, "เทวดา"),
        (_24word, "นางฟ้า"),
        (_25word, "พระพรหม"),
        (_26word, "พระอิศวร"),
        (_27word, "พระนารายณ์"),
        (_28word, "พระอินทร์"),
        (_29word, "ครุฑ"),
        (_30word, "ยักษ์"),
        (_31word, "นักบวช"),
        (_32word, "นักปราชญ์"),
        (_33word, "ผู้เชี่ยวชาญ"),
        (_34word, "เชี่ยวชาญ"),
        (_35word, "ฉลาด"),
        (_36word, "โง่"),
        (_37word, "ขี้เหนียว"),
        (_38word, "ประหยัด"),
        (_39word, "ฟุ่มเฟือย"),
        (_40word, "เอื้อเฟื้อเผื่อแผ่"),
        (_41word, "ช้าง"),
        (_42word, "ม้า"),
        (_43word, "วัว"),
        (_44word, "ควาย"),
        (_45word, "สิงโต"),
        (_46word, "เสือ"),
        (_47word, "ลิง"),
        (_48word, "นก"),
        (_49word, "นกยูง"),
        (_50word, "ปลา"),
        (_51word, "งู"),
        (_52word, "หมู"),
        (_53word, "หมา"),
        (_54word, "แมว"),
        (_55word, "จระเข้"),
        (_56word, "เต่า"),
        (_57word, "ตะพาบ"),
        (_58word, "ดอกไม้"),
        (_59word, "บัว"),
        (_60word, "หญ้า"),
        (_61word, "ต้นไม้"),
        (_62word, "ราชพฤกษ์"),
        (_63word, "กัลปพฤกษ์"),
        (_64word, "จั๋งไทย"),
        (_65word, "ขนุนปาน"),
        (_66word, "เมือง"),
        (_67word, "เมืองหลวง"),
        (_68word, "กษัตริย์"),
        (_69word, "หมอ"),
        (_70word, "โสเภณี"),
        (_71word, "คน"),
        (_72word, "ประชาชน"),
        (_73word, "ศัตรู"),
        (_74word, "ผู้หญิง"),
        (_75word, "เด็ก"),
        (_76word, "พ่อ"),
        (_77word, "แม่"),
        (_78word, "ปู่"),
        (_79word, "ย่า"),
        (_80word, "ตา"),
        (_81word, "ยาย"),
        (_82word, "ภรรยา"),
        (_83word, "สามี"),
        (_84word, "ลูก"),
        (_85word, "ลูกชาย"),
        (_86word, "ลูกสาว"),
        (_87word, "น้องชาย"),
        (_88word, "เพื่อน"),
        (_89word, "ใจ"),
        (_90word, "หัว"),
        (_91word, "ผม"),
        (_92word, "เท้า"),
        (_93word, "ตา"),
        (_94word, "คิ้ว"),
        (_95word, "ปาก"),
        (_96word, "ฟัน"),
        (_97word, "ลิ้น"),
        (_98word, "ทองคำ"),
        (_99word, "เงิน"),
        (_100word, "เพชร"),
        (_101word, "เรือ"),
        (_102word, "ธง"),
        (_103word, "หิน"),
        (_104word, "ขยะ"),
        (_105word, "แก่"),
        (_106word, "กิน"), #ฉัน เดิน:ย่าง
        (_107word, "นอน"),
        (_108word, "ป่วย"),
        (_109word, "ตาย"),
        (_110word, "ฆ่า"),
        (_111word, "ทำลาย"),
        (_112word, "สงคราม"),
        (_113word, "สนามรบ"),
        (_114word, "พยายาม"),
        (_115word, "ทำ"),
        (_116word, "เกิด"),
        (_117word, "ไหว้"),
        (_118word, "ดู"),
        (_119word, "เดิน"),
        (_120word, "ไป"),
        (_121word, "แต่งงาน"),
        (_122word, "เศร้า"),
        (_123word, "โกรธ"),
        (_124word, "สวย"),
        (_125word, "รุ่งเรือง"),
        (_126word, "เลิศ"),
        (_127word, "ขี้เหร่"),
        (_128word, "แย่"),
        (_129word, "อาหาร"),
        (_130word, "เยี่ยว"),
        (_131word, "เยี่ยว"),
        (_132word, "ขี้"),
        (_133word, "ขี้"),
        (_134word, "คำพูด"),
        (_135word, "พูด"),
        (_136word, "ทวี"),
        (_137word, "สี่"),
        (_138word, "ยี่สิบ"),
        (_139word, "กกต."),
        (_140word, "มหาวิทยาลัยขอนแก่น"),
        (_141word, "จุฬาลงกรณ์มหาวิทยาลัย"),
        (_142word, "มกราคม"),
        (_143word, "กุมภาพันธ์"),
        (_144word, "มีนาคม"),
        (_145word, "เมษายน"),
        (_146word, "พฤษภาคม"),
        (_147word, "มิถุนายน"),
        (_148word, "กรกฎาคม"),
        (_149word, "สิงหาคม"),
        (_150word, "กันยายน"),
        (_151word, "ตุลาคม"),
        (_152word, "พฤศจิกายน"),
        (_153word, "ธันวาคม"),
        (_154word, "เวลา"),
        (_155word, "กลางคืน"),
        (_156word, "กลางวัน"),
        (_157word, "วัน"),
        (_158word, "เลือด"),
        (_159word, "แดง"),
        (_160word, "ขาว"),
        (_161word, "ดำ"),
        (_162word, "ใหญ่"),
        (_163word, "อ้วน"),
        (_164word, "ผอม"),
        (_165word, "อร่อย"),
        (_166word, "เสือก"),
        (_167word, "ไม่"),
    ]
    for word in word_set
}

def process_text(text):

    for phrase, replacement in eat_words.items():
        text = text.replace(phrase, replacement)

    words = word_tokenize(text, keep_whitespace=False)

    # 🔹 แทนที่คำพ้องความหมาย
    words = [synonyms_map.get(word, word) for word in words]

    # 🔹 รวมคำสีและวันในสัปดาห์ให้เป็นคำเดียว
    merged_words = []
    i = 0
    while i < len(words):
        if i < len(words) - 1 and (words[i] + words[i + 1]) in colors:
            merged_words.append(words[i] + words[i + 1])
            i += 2
        elif i < len(words) - 1 and (words[i] + words[i + 1]) in days:
            merged_words.append(words[i] + words[i + 1])
            i += 2
        elif words[i] in time_words:
            merged_words.append(time_words[words[i]])
            i += 1
        else:
            merged_words.append(words[i])
            i += 1

    tagged_words = pos_tag(merged_words, corpus="orchid_ud")

    subject, pronoun, adverbs, verbs, objects, prepositions, others = [], [], [], [], [], [], []
    question_mark, negation = "", ""
    condition = []
    negations = []

    for idx, (word, tag) in enumerate(tagged_words):
    # 🔹 ถ้าคำก่อนหน้าเป็น "พระ" และคำปัจจุบันเป็น "ฉัน" → เปลี่ยน "ฉัน" เป็น "กิน"
        if idx > 0 and tagged_words[idx - 1][0] == "พระ" and word == "ฉัน":
            word = "กิน"

    # 🔹 ถ้าคำก่อนหน้าเป็น "พระ" และคำปัจจุบันเป็น "ไม่" → เช็คคำถัดไปเป็น "ฉัน"
        if idx > 0 and tagged_words[idx - 1][0] == "พระ" and word == "ไม่":
            if idx < len(tagged_words) - 1 and tagged_words[idx + 1][0] == "ฉัน":
                word = "กิน ไม่"  # เปลี่ยน "ไม่" เป็น "ไม่กิน"
                tagged_words[idx + 1] = ("", "")  # ลบ "ฉัน" ออกจาก list

        if word == "ถ้า":
            condition.append(word)
            continue

        if word == "ควร":
            adverbs.insert(0, word)  # ทำให้ "ควร" อยู่หน้ากริยา
            continue

        if word in adverbs_to_change:
            word = "กัน"

        if word in question_words:
            question_mark = "?"
            continue

        if word in words_to_remove:
            continue

        if word in {"ไม่"}:
            negations.append(word)
            continue

        if tag.startswith("VERB"):
            verbs.append(word)
        elif tag.startswith("ADV"):
            adverbs.append(word)
        elif tag.startswith("NOUN"):
            # แยกแยะว่าเป็น **ประธาน (subject) หรือ กรรม (object)**
            if not verbs:  # ถ้ายังไม่มี verb แสดงว่าเป็นประธาน
                subject.append(word)
            else:
                objects.append(word)
        elif tag.startswith("PRON"):
            # ถ้าคำเป็นสรรพนาม ให้วางเป็น **ประธาน**
            subject.append(word)
        elif tag.startswith("ADP"):
            prepositions.append(word)
        else:
            others.append(word)

    # 🔹 ปรับการเรียงประโยคเป็น TSL syntax
    new_sentence = condition + subject + pronoun + objects + adverbs + prepositions + others + verbs  # กริยาไปหลังสุด

    # 🔹 ให้คำว่า "ไม่" อยู่หน้ากริยา
    if negations and verbs:
        new_sentence.insert(new_sentence.index(verbs[0]), negations[0])
    elif negations:
        new_sentence += negations

    if question_mark:
        new_sentence.append(question_mark)
    # 🔹 **สลับคำ "ไม่ กิน" → "กิน ไม่"**
    for i in range(len(new_sentence) - 1):
        if new_sentence[i] == "ไม่" and new_sentence[i + 1] == "กิน":
            new_sentence[i], new_sentence[i + 1] = new_sentence[i + 1], new_sentence[i]

    return " ".join(new_sentence)

@app.route("/process", methods=["POST"])
def rearrange():
    data = request.get_json()
    text = data.get("text", "")
    transformed_text = process_text(text)
    return jsonify({"result": transformed_text})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
