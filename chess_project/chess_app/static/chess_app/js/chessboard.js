// Function to move the chess piece from source to destination
function movePiece() {
    // Get the source and destination IDs from the input fields
    const src = document.getElementById('src').value.toLowerCase();  // Ensure lowercase for input
    const dst = document.getElementById('dst').value.toLowerCase();  // Ensure lowercase for input
  
    // Validate that both source and destination are provided
    if (src && dst) {
        const srcElem = document.getElementById(src);
        const dstElem = document.getElementById(dst);
  
        // Ensure that the source square has a piece and both elements exist
        if (srcElem && dstElem && srcElem.innerHTML.trim() !== '') {
            // Move the piece to the destination
            dstElem.innerHTML = srcElem.innerHTML;
            srcElem.innerHTML = '&nbsp;';  // Clear the source square
        } else {
            alert('Invalid move: Please ensure both source and destination are valid and source contains a piece.');
        }
    } else {
        alert('Please provide both source and destination.');
    }
  }
  
  // Function to reset the chessboard to its original state
  function resetBoard() {
    // Reload the page to reset the board
    window.location.reload();
  }
  