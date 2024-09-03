from __future__ import print_function
import os.path
import base64
from email import message_from_bytes
import openai
import os
import json
import uuid
import chromadb
from chromadb.config import Settings
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

#配置持久化目录
persist_directory = "C:/Users/honma/Desktop/test"

def get_chroma_client(persist_directory):
    settings = Settings(persist_directory=persist_directory)
    client = chromadb.Client(settings=settings)
    print(f"ChromaDB 客户端已创建，持久化目录: {persist_directory}")
    return client

openai.api_key = 'sk-4gnt1Juyd8NDSU1VWaG2-NC5NGVpG24w1CYCCjrZDnT3BlbkFJlsimjDWTNFHi-17okFJUcY29YbrsAWHDqj0EcvVaMA'

# 删除旧的 token.json 文件
if os.path.exists('token.json'):
    os.remove('token.json')

# SCOPES を変更した場合、token.json ファイルを削除してください。
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']





"""「Processed」というラベルがあるかどうかを確認します。存在しない場合はタグが作成されます。"""
def get_or_create_label(service, label_name):
    try:
        # 获取所有标签
        labels_result = service.users().labels().list(userId='me').execute()
        labels = labels_result.get('labels', [])

        # 查找是否存在指定标签
        for label in labels:
            if label['name'] == label_name:
                return label['id']

        # 如果标签不存在，创建一个新的标签
        label_body = {
            'name': label_name,
            'labelListVisibility': 'labelShow',
            'messageListVisibility': 'show',
        }
        new_label = service.users().labels().create(userId='me', body=label_body).execute()
        return new_label['id']
    except HttpError as error:
        print(f'创建标签时发生错误: {error}')
        return None
    
"""メールに「Processed」ラベルを追加します"""
def add_label_to_message(service, message_id, label_id):
    try:
        service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'addLabelIds': [label_id]}
        ).execute()
        print(f'邮件 {message_id} 已标记为 Processed')
    except HttpError as error:
        print(f'为邮件添加标签时发生错误: {error}')

"""メールのすべてのラベルを取得します。"""
def get_message_labels(service, message_id):
    try:
        message = service.users().messages().get(userId='me', id=message_id).execute()
        label_ids = message.get('labelIds', [])
        return label_ids
    except HttpError as error:
        print(f'获取邮件标签时发生错误: {error}')
        return []

"""メールに「Processed」タグが付いているかどうかを確認してください。"""    
def is_message_processed(service, message_id, processed_label_id):
    labels = get_message_labels(service, message_id)
    return processed_label_id in labels


"""メール本文の内容を解析する"""
def get_message_body(msg):
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            if content_type == "text/plain" and "attachment" not in content_disposition:
                body += part.get_payload(decode=True).decode('utf-8') + "\n"
            elif content_type == "text/html" and "attachment" not in content_disposition:
                body += part.get_payload(decode=True).decode('utf-8') + "\n"
    else:
        content_type = msg.get_content_type()
        if content_type == "text/plain" or content_type == "text/html":
            body = msg.get_payload(decode=True).decode('utf-8')
    return body


"""LLM を使用してメール本文から案件情報を抽出する"""
def extract_case_info_llm(body):
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",  #  "gpt-4"を使用する，もしアクセスがある場合
            messages=[
                {"role": "system", 
                "content": f"以下のメール本文から案件情報を抽出してください：\n\n{body}\n\n抽出する情報には、案件名、作業内容、作業場所、作業期間などが含まれます。"}
            ],
            max_tokens=300,
            temperature=0.5
        )
        # print(response)
        # print(type(response.choices[0].message))
        return response.choices[0].message.content.strip()
    except Exception as e:  # 異常処理
        print(f"OpenAI API エラーが発生しました: {e}")
        return ""
    
"""案件情報をベクトル化する"""
def get_embedding(text):
    try:
        response = openai.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        embedding = response.data[0].embedding
        return embedding
    except Exception as e:
        print(f"ベクトルの取得中にエラーが発生しました: {e}")
        return None

"""ベクトルをjsonファイルに保存"""
def save_embedding_to_file(embedding, filename="embedding.json"):
    with open(filename, "w") as f:
        json.dump(embedding, f)
    print(f"ファイル {filename} からベクトルを読み込みました。")

def save_embedding_to_database(embedding, metadata, collection_name="example_collection"):
    client = get_chroma_client(persist_directory)
    try:
        collection = client.get_or_create_collection(name=collection_name)
        unique_id = str(uuid.uuid4())  # 一意のIDを生成
        print(f"保存的 embedding 数据: {embedding}")  # 调试信息
        collection.add(ids=[unique_id], embeddings=[embedding], metadatas=[metadata])
        print(f"ベクトルをデータベースに保存しました (ID: {unique_id})。")
    except Exception as e:
        print(f"データベースへの保存中にエラーが発生しました: {e}")


def list_documents_in_collection(collection_name):
    client = get_chroma_client(persist_directory)
    try:
        # 获取集合（如果不存在，则创建）
        collection = client.get_or_create_collection(name=collection_name)
        documents = collection.get()
        #print(f"コレクション '{collection_name}' 中的文档:", documents)
        if documents:
            print(f"集合 '{collection_name}' 中的文档:", documents)
        else:
            print("ドキュメントが見つかりませんでした。")
    except Exception as e:
        print(f"コレクションへのアクセス中にエラーが発生しました: {e}")


"""
def load_embedding_from_file(filename="embedding.json"):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            embedding = json.load(f)
        print(f"ファイル {filename} からベクトルを読み込みました。")
        return embedding
    else:
        print(f"ファイル {filename} が見つかりません。")
        return None
"""

def load_embeddings_from_file(file_path='embedding.json'):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            data = json.load(file)
            print(f"从文件加载的 embedding 数据: {data}")  # 调试信息
            return data
    else:
        print(f"文件 {file_path} 未找到。")
        return None


"""Gmail からメールを読み取って案件情報を抽出する方法を示す"""
def main():
    creds = None
    vector_count = 0  # 初始化计数器
    all_embeddings = {"embeddings": [], "metadatas": []}

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('C:/python_test/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('gmail', 'v1', credentials=creds)
        
        # 获取或创建“Processed”标签
        processed_label_id = get_or_create_label(service, 'Processed')
        if not processed_label_id:
            print("无法获取或创建 'Processed' 标签")
            return

        results = service.users().messages().list(userId='me', labelIds=['INBOX']).execute()
        messages = results.get('messages', [])

        if not messages:
            print('没有找到未处理的邮件。')
        else:
            for message in messages:
                message_id = message['id']

                # 检查邮件是否已经被标记为“Processed”
                if is_message_processed(service, message_id, processed_label_id):
                    #print(f'邮件 {message_id} 已经处理过，跳过。')
                    continue

                msg = service.users().messages().get(userId='me', id=message_id, format='raw').execute()
                msg_bytes = base64.urlsafe_b64decode(msg['raw'].encode('utf-8'))
                mime_msg = message_from_bytes(msg_bytes)
                
                body = get_message_body(mime_msg)
                case_info = extract_case_info_llm(body)
                
                embedding = get_embedding(case_info)
                if embedding:
                    metadata = {"email_id": message_id, "content": body}
                    #save_embedding_to_file({"embeddings": [embedding], "metadatas": [metadata]})
                    #save_embedding_to_database(embedding, metadata)
                    all_embeddings["embeddings"].append(embedding)
                    all_embeddings["metadatas"].append(metadata)

                    # 计数器递增
                    vector_count += 1

                # 将“Processed”标签添加到处理过的邮件
                add_label_to_message(service, message_id, processed_label_id)

                print("="*50)

        # 保存所有的嵌入向量到文件
        save_embedding_to_file(all_embeddings)
        
        # 检查指定集合中的文档
        collection_name = "example_collection"  # 确保这个名称与你保存向量时使用的名称一致
        list_documents_in_collection(collection_name)
        
        # 从文件加载向量并保存到数据库中
        embedding_from_file = load_embeddings_from_file()
        if embedding_from_file:
            client = get_chroma_client(persist_directory)
            collection = client.get_or_create_collection(name=collection_name)  # 确保集合存在
            for embed, meta in zip(embedding_from_file["embeddings"], embedding_from_file["metadatas"]):
                save_embedding_to_database(embed, meta)
        
        # 打印最终生成的向量数量
        print(f"总共生成了 {vector_count} 个向量。")

    except HttpError as error:
        print(f'错误发生: {error}')

if __name__ == '__main__':
    main()