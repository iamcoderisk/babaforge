"""
Custom SMTP Relay Server for sendbaba.com with TLS support
"""
import asyncio
import dns.resolver
from datetime import datetime
from typing import Optional, List, Dict, Tuple
import re
import json
import logging
import ssl

from app import redis_client
from app.services.dkim.dkim_service import DKIMService

logger = logging.getLogger(__name__)


class SMTPRelayServer:
    """Custom SMTP Relay - Sends directly to MX servers with TLS"""
    
    def __init__(self, server_ip='156.67.29.186', domain='sendbaba.com'):
        self.server_ip = server_ip
        self.domain = domain
        self.hostname = f'mail.{domain}'
        self.dkim_service = DKIMService(domain)
        self.sent_count = 0
        self.failed_count = 0
    
    async def get_mx_records(self, domain: str) -> List[Tuple[int, str]]:
        """Get MX records with caching"""
        cache_key = f'mx:{domain}'
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
        
        try:
            answers = dns.resolver.resolve(domain, 'MX')
            mx_records = []
            for rdata in answers:
                priority = rdata.preference
                mx_host = str(rdata.exchange).rstrip('.')
                mx_records.append((priority, mx_host))
            
            mx_records.sort(key=lambda x: x[0])
            redis_client.setex(cache_key, 3600, json.dumps(mx_records))
            logger.info(f"MX records for {domain}: {mx_records}")
            return mx_records
        except Exception as e:
            logger.warning(f"No MX for {domain}, using domain directly: {e}")
            return [(10, domain)]
    
    async def connect_to_mx(self, mx_host: str, port: int = 25):
        """Connect to MX server with STARTTLS support"""
        try:
            # Initial connection
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(mx_host, port),
                timeout=30
            )
            
            greeting = await asyncio.wait_for(reader.readline(), timeout=10)
            logger.info(f"Connected to {mx_host}: {greeting.decode().strip()}")
            
            # Send EHLO
            writer.write(f'EHLO {self.hostname}\r\n'.encode())
            await writer.drain()
            
            # Read EHLO response and check for STARTTLS
            supports_starttls = False
            while True:
                line = await asyncio.wait_for(reader.readline(), timeout=10)
                response = line.decode().strip()
                if 'STARTTLS' in response.upper():
                    supports_starttls = True
                if not response.startswith('250-'):
                    break
            
            # Upgrade to TLS if supported
            if supports_starttls:
                logger.info(f"Starting TLS with {mx_host}")
                writer.write(b'STARTTLS\r\n')
                await writer.drain()
                
                response = await asyncio.wait_for(reader.readline(), timeout=10)
                if response.decode().startswith('220'):
                    # Create SSL context
                    ssl_context = ssl.create_default_context()
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE
                    
                    # Get the transport and upgrade to TLS
                    transport = writer.transport
                    protocol = transport.get_protocol()
                    
                    # Upgrade connection to TLS
                    loop = asyncio.get_event_loop()
                    new_transport = await loop.start_tls(
                        transport, protocol, ssl_context,
                        server_hostname=mx_host
                    )
                    
                    # Create new reader/writer with TLS
                    reader = asyncio.StreamReader()
                    protocol = asyncio.StreamReaderProtocol(reader)
                    new_transport.set_protocol(protocol)
                    writer = asyncio.StreamWriter(new_transport, protocol, reader, loop)
                    
                    # Send EHLO again after TLS
                    writer.write(f'EHLO {self.hostname}\r\n'.encode())
                    await writer.drain()
                    
                    while True:
                        line = await asyncio.wait_for(reader.readline(), timeout=10)
                        response = line.decode().strip()
                        if not response.startswith('250-'):
                            break
                    
                    logger.info(f"TLS established with {mx_host}")
                else:
                    logger.warning(f"STARTTLS failed on {mx_host}, continuing without TLS")
            else:
                logger.warning(f"STARTTLS not supported by {mx_host}")
            
            return reader, writer
        except Exception as e:
            logger.error(f"Error connecting to {mx_host}: {e}")
            return None, None
    
    async def send_smtp_command(self, writer, reader, command: str, expected='250'):
        """Send SMTP command and get response"""
        try:
            writer.write(f'{command}\r\n'.encode())
            await writer.drain()
            
            response = await asyncio.wait_for(reader.readline(), timeout=30)
            response_str = response.decode().strip()
            logger.debug(f"Command: {command[:50]}... Response: {response_str}")
            
            return response_str.startswith(expected), response_str
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            return False, str(e)
    
    async def send_email(self, email_data: Dict) -> Dict:
        """Send email through SMTP relay"""
        email_id = email_data.get('id')
        recipient = email_data.get('to')
        sender = email_data.get('from')
        
        recipient_domain = recipient.split('@')[1] if '@' in recipient else None
        if not recipient_domain:
            return {
                'success': False,
                'message': 'Invalid recipient',
                'bounce': True,
                'bounce_type': 'hard'
            }
        
        logger.info(f"Sending email {email_id} to {recipient}")
        
        mx_records = await self.get_mx_records(recipient_domain)
        if not mx_records:
            return {
                'success': False,
                'message': f'No MX records for {recipient_domain}',
                'bounce': True,
                'bounce_type': 'hard'
            }
        
        for priority, mx_host in mx_records:
            logger.info(f"Trying MX: {mx_host} (priority {priority})")
            
            reader, writer = await self.connect_to_mx(mx_host)
            if not reader or not writer:
                continue
            
            try:
                # MAIL FROM
                success, response = await self.send_smtp_command(
                    writer, reader, f'MAIL FROM:<{sender}>'
                )
                if not success:
                    if response.startswith('5'):
                        writer.close()
                        await writer.wait_closed()
                        return {
                            'success': False,
                            'message': response,
                            'bounce': True,
                            'bounce_type': 'hard'
                        }
                    continue
                
                # RCPT TO
                success, response = await self.send_smtp_command(
                    writer, reader, f'RCPT TO:<{recipient}>'
                )
                if not success:
                    if response.startswith('5'):
                        writer.close()
                        await writer.wait_closed()
                        return {
                            'success': False,
                            'message': response,
                            'bounce': True,
                            'bounce_type': 'hard'
                        }
                    continue
                
                # DATA
                success, response = await self.send_smtp_command(
                    writer, reader, 'DATA', '354'
                )
                if not success:
                    continue
                
                # Build message
                message = self.build_message(email_data)
                
                # Sign with DKIM
                try:
                    full_message = self.dkim_service.sign_email(message)
                except Exception as e:
                    logger.warning(f"DKIM signing failed: {e}")
                    full_message = message.encode() if isinstance(message, str) else message
                
                # Send message
                writer.write(full_message)
                writer.write(b'\r\n.\r\n')
                await writer.drain()
                
                # Get response
                response = await asyncio.wait_for(reader.readline(), timeout=60)
                response_str = response.decode().strip()
                
                logger.info(f"Email {email_id} response: {response_str}")
                
                # Close
                writer.write(b'QUIT\r\n')
                await writer.drain()
                writer.close()
                await writer.wait_closed()
                
                if response_str.startswith('250'):
                    self.sent_count += 1
                    redis_client.incr('metrics:sent:total')
                    redis_client.incr(f'metrics:sent:domain:{recipient_domain}')
                    
                    return {
                        'success': True,
                        'message': response_str,
                        'bounce': False,
                        'mx_server': mx_host
                    }
                else:
                    return {
                        'success': False,
                        'message': response_str,
                        'bounce': False
                    }
            
            except Exception as e:
                logger.error(f"Error sending to {mx_host}: {e}")
                try:
                    writer.close()
                    await writer.wait_closed()
                except:
                    pass
                continue
        
        self.failed_count += 1
        return {
            'success': False,
            'message': 'All MX servers failed',
            'bounce': False
        }
    
    def build_message(self, email_data: Dict) -> str:
        """Build RFC 5322 compliant message"""
        lines = []
        lines.append(f"From: {email_data.get('from')}")
        lines.append(f"To: {email_data.get('to')}")
        lines.append(f"Subject: {email_data.get('subject', '(no subject)')}")
        lines.append(f"Date: {datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')}")
        lines.append(f"Message-ID: <{email_data.get('id')}@{self.domain}>")
        lines.append("Content-Type: text/plain; charset=utf-8")
        lines.append("")
        lines.append(email_data.get('text_body', ''))
        
        return '\r\n'.join(lines)


class SMTPBounceReceiver:
    """SMTP server to receive bounces on port 25"""
    
    def __init__(self, listen_ip='0.0.0.0', listen_port=25, domain='sendbaba.com'):
        self.listen_ip = listen_ip
        self.listen_port = listen_port
        self.domain = domain
    
    async def handle_client(self, reader, writer):
        """Handle incoming bounce connection"""
        addr = writer.get_extra_info('peername')
        logger.info(f"Bounce connection from {addr}")
        
        try:
            writer.write(f'220 {self.domain} ESMTP Bounce Handler\r\n'.encode())
            await writer.drain()
            
            mail_from = None
            message_data = []
            in_data = False
            
            while True:
                line = await asyncio.wait_for(reader.readline(), timeout=300)
                if not line:
                    break
                
                command = line.decode().strip()
                
                if in_data:
                    if command == '.':
                        in_data = False
                        full_message = '\r\n'.join(message_data)
                        await self.process_bounce(full_message, mail_from)
                        writer.write(b'250 OK Message accepted\r\n')
                        await writer.drain()
                        message_data = []
                    else:
                        message_data.append(command)
                    continue
                
                cmd = command.upper()
                
                if cmd.startswith('EHLO') or cmd.startswith('HELO'):
                    writer.write(f'250 {self.domain}\r\n'.encode())
                elif cmd.startswith('MAIL FROM:'):
                    match = re.search(r'<(.+?)>', command)
                    mail_from = match.group(1) if match else ''
                    writer.write(b'250 OK\r\n')
                elif cmd.startswith('RCPT TO:'):
                    writer.write(b'250 OK\r\n')
                elif cmd == 'DATA':
                    writer.write(b'354 Start mail input\r\n')
                    in_data = True
                elif cmd == 'QUIT':
                    writer.write(b'221 Bye\r\n')
                    break
                else:
                    writer.write(b'250 OK\r\n')
                
                await writer.drain()
        
        except Exception as e:
            logger.error(f"Bounce handler error: {e}")
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except:
                pass
    
    async def process_bounce(self, message: str, mail_from: str):
        """Process bounce message"""
        logger.info(f"Processing bounce from {mail_from}")
        
        try:
            bounce_data = {
                'from': mail_from,
                'message_preview': message[:500],
                'timestamp': datetime.utcnow().isoformat()
            }
            
            redis_client.lpush('bounces:received', json.dumps(bounce_data))
            redis_client.ltrim('bounces:received', 0, 999)
            redis_client.incr('metrics:bounced:total')
            
            logger.info("Bounce processed and stored")
        except Exception as e:
            logger.error(f"Error processing bounce: {e}")
    
    async def start(self):
        """Start bounce receiver server"""
        server = await asyncio.start_server(
            self.handle_client,
            self.listen_ip,
            self.listen_port
        )
        
        addr = server.sockets[0].getsockname()
        logger.info(f'Bounce receiver listening on {addr}')
        
        async with server:
            await server.serve_forever()


async def send_via_relay(email_data: Dict) -> Dict:
    """Send email via custom relay - called by workers"""
    relay = SMTPRelayServer(
        server_ip='156.67.29.186',
        domain='sendbaba.com'
    )
    return await relay.send_email(email_data)