
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# SMTP服务器配置（以Gmail为例）
smtp_server = "smtp.gmail.com"
smtp_port = 587
smtp_user = "w.xiaomeng0329@gmail.com"
smtp_password = "bzqe okzh ilhz yyup"

# 收件人信息
recipient_email = "jyjeigyou@gmail.com"
subject = "FW: ★急募★注力案da33246"
body = """

--- 案件情報 -----------------------------------------------------------
【案件名】　　：車載ECU車両制御のアプリケーション開発
【作業場所】　：みなとみらい（常駐）
【勤務時間】　：9:00 - 18:00 ※昼休憩1時間
【作業期間】　：24年8月中旬頃～長期
【募集人数】　：1名～2名（同所属、ベテラン or 経験者と若手技術者（未経験不可）からのセット歓迎
【要求スキル】 ：
　　　　　　　【必須】
　　　　　　　　・組込経験である方
　　　　　　　　・C、C++経験のある方
　　　　　　　　・コミュニケーションを円滑に取ることができる方
　　　　　　　【尚可】
　　　　　　　　・要件のすり合わせ、設計、実装、試験まで実施できる方
　　　　　　　　・NXPマイコンの開発経験がある方
　　　　　　　　・複雑なソフトウェアを分析し、綺麗にコーディングできる方
【単　　価】　：スキル見合い　※ご希望額をご提示ください
【契約形態】　：準委任 or 派遣
【清　　算】　：固定
【商　　流】　：貴社正社員様まで。個人事業主、外国籍不可。
【年　　齢】　：40代まで。新人は受け入れ不可。
【面談回数】　：最大2回(弊社、案件元会社様)
【備　　考】　：★弊社プロパ参画中のお客様です★
　　　　　　　　健康面に問題なく、勤怠良好な方
　　　　　　　　自発的に動き、積極的にコミュニケーションが取れる方


------------------------------------------------------------◩
"""

# 创建SMTP会话
server = smtplib.SMTP(smtp_server, smtp_port)
server.starttls()  # 启用TLS加密
server.login(smtp_user, smtp_password)

# 发送1000封邮件
for i in range(3):
    msg = MIMEMultipart()
    msg["From"] = smtp_user
    msg["To"] = recipient_email
    msg["Subject"] = f"{subject} #{i+1}"

    msg.attach(MIMEText(body, "plain"))

    try:
        server.sendmail(smtp_user, recipient_email, msg.as_string())
        print(f"Email {i+1} sent successfully")
    except Exception as e:
        print(f"Failed to send email {i+1}: {str(e)}")

# 关闭SMTP会话
server.quit()
