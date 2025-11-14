"""
SMTP Submission Server (Port 587)
Accepts Laravel and other SMTP clients
"""
import asyncio
import base64
import uuid
import json
import logging
from datetime import datetime
from app.smtp.relay_server import send_via_relay
from app import redis_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SMTPSubmissionServer:
    """SMTP server for client submissions"""
    
    def __init__(self, listen_ip='0.0.0.0', listen_port=587):
        self.listen_ip = listen_ip
        self.listen_port = listen_port
        
        # Valid credentials - CHANGE THESE!
        self.valid_users = {
            'sendbaba': 'SecurePassword123!',
            'laravel': 'Laravel2024Password!'
        }
    
    async def handle_client(self, reader, writer):
        """Handle SMTP client"""
        addr = writer.get_extra_info('peername')
        logger.info(f"SMTP connection from {addr}")
        
        authenticated = False
        mail_from = None
        rcpt_to = []
        message_data = []
        in_data = False
        
        try:
            # Greeting
            writer.write(b'220 mail.sendbaba.com ESMTP Ready\r\n')
            await writer.drain()
            
            while True:
                line = await asyncio.wait_for(reader.readline(), timeout=300)
                if not line:
                    break
                
                command = line.decode('utf-8', errors='ignore').strip()
                cmd_upper = command.upper()
                
                logger.debug(f"Received: {command}")
                
                if in_data:
                    if command == '.':
                        # Message complete - send it!
                        await self.process_message(mail_from, rcpt_to, message_data, writer)
                        
                        # Reset
                        in_data = False
                        message_data = []
                        mail_from = None
                        rcpt_to = []
                    else:
                        message_data.append(command)
                    continue
                
                # Handle SMTP commands
                if cmd_upper.startswith('EHLO') or cmd_upper.startswith('HELO'):
                    hostname = command.split()[1] if len(command.split()) > 1 else 'client'
                    writer.write(b'250-mail.sendbaba.com Hello ' + hostname.encode() + b'\r\n')
                    writer.write(b'250-AUTH LOGIN PLAIN\r\n')
                    writer.write(b'250-SIZE 52428800\r\n')  # 50MB
                    writer.write(b'250 HELP\r\n')
                
                elif cmd_upper.startswith('AUTH LOGIN'):
                    # Username prompt
                    writer.write(b'334 VXNlcm5hbWU6\r\n')  # Base64 "Username:"
                    await writer.drain()
                    
                    username_line = await reader.readline()
                    try:
                        username = base64.b64decode(username_line.strip()).decode()
                    except:
                        username = username_line.decode().strip()
                    
                    # Password prompt
                    writer.write(b'334 UGFzc3dvcmQ6\r\n')  # Base64 "Password:"
                    await writer.drain()
                    
                    password_line = await reader.readline()
                    try:
                        password = base64.b64decode(password_line.strip()).decode()
                    except:
                        password = password_line.decode().strip()
                    
                    # Check credentials
                    if username in self.valid_users and self.valid_users[username] == password:
                        authenticated = True
                        writer.write(b'235 2.7.0 Authentication successful\r\n')
                        logger.info(f"User {username} authenticated")
                    else:
                        writer.write(b'535 5.7.8 Authentication failed\r\n')
                        logger.warning(f"Failed auth attempt: {username}")
                
                elif cmd_upper.startswith('AUTH PLAIN'):
                    # Handle PLAIN auth
                    parts = command.split(' ', 2)
                    if len(parts) == 3:
                        try:
                            credentials = base64.b64decode(parts[2]).decode().split('\x00')
                            username = credentials[1] if len(credentials) > 1 else ''
                            password = credentials[2] if len(credentials) > 2 else ''
                            
                            if username in self.valid_users and self.valid_users[username] == password:
                                authenticated = True
                                writer.write(b'235 2.7.0 Authentication successful\r\n')
                            else:
                                writer.write(b'535 5.7.8 Authentication failed\r\n')
                        except:
                            writer.write(b'535 5.7.8 Authentication failed\r\n')
                    else:
                        writer.write(b'334 \r\n')
                        auth_line = await reader.readline()
                        # Process auth...
                        writer.write(b'235 2.7.0 Authentication successful\r\n')
                
                elif cmd_upper.startswith('MAIL FROM:'):
                    if not authenticated:
                        writer.write(b'530 5.7.0 Authentication required\r\n')
                    else:
                        # Extract email from MAIL FROM:<email@domain.com>
                        import re
                        match = re.search(r'<(.+?)>', command)
                        mail_from = match.group(1) if match else command.split(':')[1].strip()
                        writer.write(b'250 2.1.0 OK\r\n')
                
                elif cmd_upper.startswith('RCPT TO:'):
                    if not authenticated:
                        writer.write(b'530 5.7.0 Authentication required\r\n')
                    else:
                        import re
                        match = re.search(r'<(.+?)>', command)
                        rcpt = match.group(1) if match else command.split(':')[1].strip()
                        rcpt_to.append(rcpt)
                        writer.write(b'250 2.1.5 OK\r\n')
                
                elif cmd_upper == 'DATA':
                    if not authenticated:
                        writer.write(b'530 5.7.0 Authentication required\r\n')
                    else:
                        writer.write(b'354 End data with <CR><LF>.<CR><LF>\r\n')
                        in_data = True
                
                elif cmd_upper == 'QUIT':
                    writer.write(b'221 2.0.0 Bye\r\n')
                    break
                
                elif cmd_upper == 'RSET':
                    mail_from = None
                    rcpt_to = []
                    message_data = []
                    writer.write(b'250 2.0.0 OK\r\n')
                
                elif cmd_upper == 'NOOP':
                    writer.write(b'250 2.0.0 OK\r\n')
                
                else:
                    writer.write(b'502 5.5.2 Command not implemented\r\n')
                
                await writer.drain()
        
        except asyncio.TimeoutError:
            logger.warning(f"Timeout from {addr}")
        except Exception as e:
            logger.error(f"SMTP error from {addr}: {e}")
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except:
                pass
    
    async def process_message(self, mail_from, rcpt_to, message_data, writer):
        """Process and send message"""
        try:
            email_id = str(uuid.uuid4())
            
            # Parse message headers and body
            full_message = '\r\n'.join(message_data)
            
            # Extract subject from headers
            subject = ''
            for line in message_data:
                if line.lower().startswith('subject:'):
                    subject = line.split(':', 1)[1].strip()
                    break
            
            # Queue email
            email_data = {
                'id': email_id,
                'from': mail_from,
                'to': rcpt_to[0] if rcpt_to else '',
                'subject': subject,
                'text_body': full_message,  # Full message with headers
                'priority': 5,
                'created_at': datetime.utcnow().isoformat()
            }
            
            # Add to Redis queue
            redis_client.lpush('outgoing_5', json.dumps(email_data))
            
            writer.write(f'250 2.0.0 OK: queued as {email_id}\r\n'.encode())
            logger.info(f"Queued email {email_id} from {mail_from} to {rcpt_to}")
        
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            writer.write(b'554 5.3.0 Transaction failed\r\n')
        
        await writer.drain()
    
    async def start(self):
        """Start SMTP submission server"""
        server = await asyncio.start_server(
            self.handle_client,
            self.listen_ip,
            self.listen_port
        )
        
        logger.info(f'SMTP Submission Server listening on {self.listen_ip}:{self.listen_port}')
        logger.info('Waiting for Laravel and other SMTP clients...')
        
        async with server:
            await server.serve_forever()


async def main():
    server = SMTPSubmissionServer(listen_ip='0.0.0.0', listen_port=587)
    await server.start()


if __name__ == '__main__':
    asyncio.run(main())
