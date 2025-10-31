<?php
// File: SendbabaMailer.php

class SendbabaMailer {
    private $api_url = 'https://sendbaba.com/api/v1/send';
    private $api_key = null; // Optional: add API key auth later
    
    public function send($to, $from, $subject, $body, $html = null, $priority = 5) {
        $data = array(
            'to' => $to,
            'from' => $from,
            'subject' => $subject,
            'text_body' => $body,
            'priority' => $priority
        );
        
        if ($html) {
            $data['html_body'] = $html;
        }
        
        $ch = curl_init($this->api_url);
        curl_setopt($ch, CURLOPT_POST, 1);
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
        curl_setopt($ch, CURLOPT_HTTPHEADER, array(
            'Content-Type: application/json',
            // 'Authorization: Bearer ' . $this->api_key  // Optional
        ));
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        
        $response = curl_exec($ch);
        $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        $result = json_decode($response, true);
        
        if ($http_code == 200 && $result['success']) {
            return array(
                'success' => true,
                'email_id' => $result['email_id']
            );
        } else {
            return array(
                'success' => false,
                'error' => $result['error'] ?? 'Unknown error'
            );
        }
    }
    
    public function sendBulk($emails) {
        $data = array('emails' => $emails);
        
        $ch = curl_init($this->api_url . '/bulk');
        curl_setopt($ch, CURLOPT_POST, 1);
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
        curl_setopt($ch, CURLOPT_HTTPHEADER, array('Content-Type: application/json'));
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        
        $response = curl_exec($ch);
        curl_close($ch);
        
        return json_decode($response, true);
    }
}

// Usage:
$mailer = new SendbabaMailer();

$result = $mailer->send(
    'ekeminyd@gmail.com',
    'hello@sendbaba.com',
    'Welcome Email',
    'Plain text body',
    '<h1>HTML body</h1>',
    5  // priority
);

if ($result['success']) {
    echo "Sent! Email ID: " . $result['email_id'];
} else {
    echo "Failed: " . $result['error'];
}
?>
