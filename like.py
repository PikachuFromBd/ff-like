import asyncio
import json
import binascii
import argparse
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from google.protobuf.json_format import MessageToJson
import aiohttp
import requests
import like_pb2
import like_count_pb2
import uid_generator_pb2
from google.protobuf.message import DecodeError

class FreeFireLikeBot:
    def __init__(self):
        self.tokens_cache = {}
    
    def load_tokens(self, server_name):
        try:
            if server_name in self.tokens_cache:
                return self.tokens_cache[server_name]
                
            if server_name == "IND":
                with open("token_ind.json", "r") as f:
                    tokens = json.load(f)
            elif server_name in {"BR", "US", "SAC", "NA"}:
                with open("token_br.json", "r") as f:
                    tokens = json.load(f)
            else:
                with open("token_bd.json", "r") as f:
                    tokens = json.load(f)
            
            self.tokens_cache[server_name] = tokens
            return tokens
        except Exception as e:
            print(f"❌ Error loading tokens for server {server_name}: {e}")
            return None

    def encrypt_message(self, plaintext):
        try:
            key = b'Yg&tc%DEuh6%Zc^8'
            iv = b'6oyZDr22E3ychjM%'
            cipher = AES.new(key, AES.MODE_CBC, iv)
            padded_message = pad(plaintext, AES.block_size)
            encrypted_message = cipher.encrypt(padded_message)
            return binascii.hexlify(encrypted_message).decode('utf-8')
        except Exception as e:
            print(f"❌ Error encrypting message: {e}")
            return None

    def create_protobuf_message(self, user_id, region):
        try:
            message = like_pb2.like()
            message.uid = int(user_id)
            message.region = region
            return message.SerializeToString()
        except Exception as e:
            print(f"❌ Error creating protobuf message: {e}")
            return None

    async def send_request(self, encrypted_uid, token, url):
        try:
            edata = bytes.fromhex(encrypted_uid)
            headers = {
                'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)",
                'Connection': "Keep-Alive",
                'Accept-Encoding': "gzip",
                'Authorization': f"Bearer {token}",
                'Content-Type': "application/x-www-form-urlencoded",
                'Expect': "100-continue",
                'X-Unity-Version': "2018.4.11f1",
                'X-GA': "v1 1",
                'ReleaseVersion': "OB50"
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=edata, headers=headers) as response:
                    if response.status != 200:
                        print(f"❌ Request failed with status code: {response.status}")
                        return response.status
                    return await response.text()
        except Exception as e:
            print(f"❌ Exception in send_request: {e}")
            return None

    async def send_multiple_requests(self, uid, server_name, url, count=100):
        try:
            region = server_name
            protobuf_message = self.create_protobuf_message(uid, region)
            if protobuf_message is None:
                print("❌ Failed to create protobuf message.")
                return None
            
            encrypted_uid = self.encrypt_message(protobuf_message)
            if encrypted_uid is None:
                print("❌ Encryption failed.")
                return None
            
            tokens = self.load_tokens(server_name)
            if tokens is None:
                print("❌ Failed to load tokens.")
                return None
            
            print(f"🔄 Sending {count} like requests...")
            tasks = []
            for i in range(count):
                token = tokens[i % len(tokens)]["token"]
                tasks.append(self.send_request(encrypted_uid, token, url))
            
            # Show progress
            for i, task in enumerate(asyncio.as_completed(tasks)):
                await task
                if (i + 1) % 10 == 0:
                    print(f"📤 Sent {i + 1}/{count} requests")
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return results
        except Exception as e:
            print(f"❌ Exception in send_multiple_requests: {e}")
            return None

    def create_protobuf(self, uid):
        try:
            message = uid_generator_pb2.uid_generator()
            message.saturn_ = int(uid)
            message.garena = 1
            return message.SerializeToString()
        except Exception as e:
            print(f"❌ Error creating uid protobuf: {e}")
            return None

    def enc(self, uid):
        protobuf_data = self.create_protobuf(uid)
        if protobuf_data is None:
            return None
        encrypted_uid = self.encrypt_message(protobuf_data)
        return encrypted_uid

    def make_request(self, encrypt, server_name, token):
        try:
            if server_name == "IND":
                url = "https://client.ind.freefiremobile.com/GetPlayerPersonalShow"
            elif server_name in {"BR", "US", "SAC", "NA"}:
                url = "https://client.us.freefiremobile.com/GetPlayerPersonalShow"
            else:
                url = "https://clientbp.ggblueshark.com/GetPlayerPersonalShow"
            
            edata = bytes.fromhex(encrypt)
            headers = {
                'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)",
                'Connection': "Keep-Alive",
                'Accept-Encoding': "gzip",
                'Authorization': f"Bearer {token}",
                'Content-Type': "application/x-www-form-urlencoded",
                'Expect': "100-continue",
                'X-Unity-Version': "2018.4.11f1",
                'X-GA': "v1 1",
                'ReleaseVersion': "OB50"
            }
            response = requests.post(url, data=edata, headers=headers, verify=False)
            hex_data = response.content.hex()
            binary = bytes.fromhex(hex_data)
            decode = self.decode_protobuf(binary)
            if decode is None:
                print("❌ Protobuf decoding returned None.")
            return decode
        except Exception as e:
            print(f"❌ Error in make_request: {e}")
            return None

    def decode_protobuf(self, binary):
        try:
            items = like_count_pb2.Info()
            items.ParseFromString(binary)
            return items
        except DecodeError as e:
            print(f"❌ Error decoding Protobuf data: {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error during protobuf decoding: {e}")
            return None

    def display_result(self, result):
        print("\n" + "="*50)
        print("🎯 FREE FIRE LIKE BOT - RESULTS")
        print("="*50)
        print(f"👤 Player Nickname: {result['PlayerNickname']}")
        print(f"🆔 Player UID: {result['UID']}")
        print(f"❤️  Likes Before Command: {result['LikesbeforeCommand']}")
        print(f"❤️  Likes After Command: {result['LikesafterCommand']}")
        print(f"🚀 Likes Given by API: {result['LikesGivenByAPI']}")
        print(f"📊 Status: {'Success' if result['status'] == 1 else 'Failed'}")
        print("="*50)

    async def process_like_request(self, uid, server_name, like_count=100):
        try:
            print(f"🎯 Starting like process for UID: {uid}, Server: {server_name}")
            
            tokens = self.load_tokens(server_name)
            if tokens is None:
                raise Exception("Failed to load tokens.")
            
            token = tokens[0]['token']
            encrypted_uid = self.enc(uid)
            if encrypted_uid is None:
                raise Exception("Encryption of UID failed.")

            # Get initial like count
            print("📊 Getting initial player info...")
            before = self.make_request(encrypted_uid, server_name, token)
            if before is None:
                raise Exception("Failed to retrieve initial player info.")
            
            try:
                jsone = MessageToJson(before)
            except Exception as e:
                raise Exception(f"Error converting 'before' protobuf to JSON: {e}")
            
            data_before = json.loads(jsone)
            before_like = data_before.get('AccountInfo', {}).get('Likes', 0)
            try:
                before_like = int(before_like)
            except Exception:
                before_like = 0
            
            print(f"❤️  Likes before command: {before_like}")

            # Determine URL for like requests
            if server_name == "IND":
                url = "https://client.ind.freefiremobile.com/LikeProfile"
            elif server_name in {"BR", "US", "SAC", "NA"}:
                url = "https://client.us.freefiremobile.com/LikeProfile"
            else:
                url = "https://clientbp.ggblueshark.com/LikeProfile"

            # Send like requests
            await self.send_multiple_requests(uid, server_name, url, like_count)

            # Get updated like count
            print("📊 Getting updated player info...")
            after = self.make_request(encrypted_uid, server_name, token)
            if after is None:
                raise Exception("Failed to retrieve player info after like requests.")
            
            try:
                jsone_after = MessageToJson(after)
            except Exception as e:
                raise Exception(f"Error converting 'after' protobuf to JSON: {e}")
            
            data_after = json.loads(jsone_after)
            after_like = int(data_after.get('AccountInfo', {}).get('Likes', 0))
            player_uid = int(data_after.get('AccountInfo', {}).get('UID', 0))
            player_name = str(data_after.get('AccountInfo', {}).get('PlayerNickname', ''))
            like_given = after_like - before_like
            status = 1 if like_given != 0 else 2
            
            result = {
                "LikesGivenByAPI": like_given,
                "LikesafterCommand": after_like,
                "LikesbeforeCommand": before_like,
                "PlayerNickname": player_name,
                "UID": player_uid,
                "status": status
            }
            
            return result
            
        except Exception as e:
            print(f"❌ Error processing request: {e}")
            return None

def main():
    parser = argparse.ArgumentParser(description='Free Fire Like Bot CLI')
    parser.add_argument('--uid', required=True, help='Player UID')
    parser.add_argument('--server', required=True, 
                       choices=['IND', 'BR', 'US', 'SAC', 'NA', 'BD'],
                       help='Server name')
    parser.add_argument('--count', type=int, default=100,
                       help='Number of likes to send (default: 100)')
    
    args = parser.parse_args()
    
    bot = FreeFireLikeBot()
    
    print("🚀 Free Fire Like Bot - CLI Version")
    print("="*40)
    
    try:
        result = asyncio.run(bot.process_like_request(args.uid, args.server, args.count))
        
        if result:
            bot.display_result(result)
        else:
            print("❌ Failed to process like request")
            
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == '__main__':
    main()