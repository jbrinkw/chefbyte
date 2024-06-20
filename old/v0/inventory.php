$servername = "localhost";
$username = "root"; // Best practice is to use a less privileged user
$password = "3YBaw=XdYGYR"; // Replace 'your_password' with your actual password

// Create connection
$conn = new mysqli($servername, $username, $password, "inventorydb");

// Check connection
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

// SQL to fetch data
$sql = "SELECT id, name, quantity, expiration_date FROM items";
$result = $conn->query($sql);

$data = array();

if ($result->num_rows > 0) {
    // output data of each row
    while($row = $result->fetch_assoc()) {
        $data[] = $row;
    }
    // Encode data as JSON
    echo json_encode(array('data' => $data));
} else {
    echo json_encode(array('data' => []));
}
$conn->close();