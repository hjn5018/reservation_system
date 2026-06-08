<?php
require_once 'config.php';

class ApiClient {
    private static function sendRequest($url, $method = 'GET', $data = null) {
        $ch = curl_init($url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $method);
        curl_setopt($ch, CURLOPT_TIMEOUT, 5);

        if ($data !== null) {
            $jsonData = json_encode($data);
            curl_setopt($ch, CURLOPT_POSTFIELDS, $jsonData);
            curl_setopt($ch, CURLOPT_HTTPHEADER, array(
                'Content-Type: application/json',
                'Content-Length: ' . strlen($jsonData)
            ));
        }

        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        
        if (curl_errno($ch)) {
            $error_msg = curl_error($ch);
            curl_close($ch);
            return array(
                "result" => "error",
                "message" => "cURL Error: " . $error_msg,
                "http_code" => 0
            );
        }

        curl_close($ch);
        
        $decoded = json_decode($response, true);
        if ($decoded === null) {
            return array(
                "result" => "error",
                "message" => "Failed to parse JSON response: " . $response,
                "http_code" => $httpCode
            );
        }

        return array(
            "result" => "success",
            "data" => $decoded,
            "http_code" => $httpCode
        );
    }

    public static function getReservations() {
        return self::sendRequest(API_BASE_URL . '/reservations', 'GET');
    }

    public static function addReservation($title, $startTime, $endTime) {
        $data = array(
            'title' => $title,
            'start_time' => $startTime,
            'end_time' => $endTime
        );
        return self::sendRequest(API_BASE_URL . '/reservations', 'POST', $data);
    }

    public static function deleteReservation($id) {
        return self::sendRequest(API_BASE_URL . '/reservations/' . $id, 'DELETE');
    }

    public static function getStatus() {
        return self::sendRequest(API_BASE_URL . '/status', 'GET');
    }

    /**
     * Pi B의 TCP 9000 포트로 직접 긴급 상태 제어 명령을 발송합니다.
     */
    public static function forceStatusSocket($status) {
        $host = SOCKET_HOST;
        $port = SOCKET_PORT;
        
        // socket 커넥션 타임아웃 3초
        $fp = @fsockopen($host, $port, $errno, $errstr, 3);
        if (!$fp) {
            return array(
                "result" => "error",
                "message" => "Socket connection failed: [$errno] $errstr"
            );
        }

        $cmd = array(
            "command" => "force_status",
            "status" => $status
        );
        
        $payload = json_encode($cmd) . "\n";
        
        fwrite($fp, $payload);
        
        $response = "";
        stream_set_timeout($fp, 3);
        while (!feof($fp)) {
            $line = fgets($fp, 1024);
            if ($line === false) break;
            $response .= $line;
        }
        
        fclose($fp);
        
        $decoded = json_decode(trim($response), true);
        if ($decoded === null) {
            return array(
                "result" => "error",
                "message" => "Invalid socket response: " . $response
            );
        }

        return $decoded;
    }
}
?>
