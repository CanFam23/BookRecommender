// Global variable to store book titles fetched from the server
let bookTitles; 

// Event listener that runs when the DOM content is fully loaded
document.addEventListener("DOMContentLoaded", function () {
  // Fetch the list of book titles from the server
  fetch("/getBookList", {
    method: "GET",
  })
    .then((response) => response.json()) // Convert response to JSON
    .then((data) => {
      bookTitles = data.bookTitles; // Store book titles globally
    })
    .catch((error) => console.error("Error fetching book list:", error)); // Handle fetch errors
});

// Event listener for form submission
document.addEventListener("DOMContentLoaded", function () {
  document
    .getElementById("bookForm")
    .addEventListener("submit", function (event) {
      event.preventDefault(); // Prevent form reload

      const bookGrid = document.getElementById("bookGrid");
      bookGrid.innerHTML = ""; // Clear previous results

      removeErrorMessage(); // Remove any existing error messages

      let nameValue = document.getElementById("searchBox").value;

      // Check if the entered book title exists in the fetched list
      let bookFound = bookTitles.includes(nameValue);
      if (!bookFound) {
        displayError(`No book found with name '${nameValue}'`);
        return; // Exit if book is not found
      }

      // Send a POST request to fetch book details
      fetch("/getBooks", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ name: nameValue }),
      })
        .then((response) => response.json()) // Convert response to JSON
        .then((data) => {
          console.log(data.bookList); // Log the list of books
          console.log(data.bookData); // Log detailed book data

          // Iterate over each book title in the fetched list
          data.bookList.forEach((title) => {
            // Find the corresponding book data
            let book = data.bookData.find((book) => removePunctuation(book.Title) === title);

            console.log(`${book}`); // Log book details

            if (book) {
              // Create a new book item element
              let bookItem = document.createElement("div");
              bookItem.classList.add("grid-item");

              // Populate the book item with details
              bookItem.innerHTML = `
                        <h3 class="bookTitle">${
                          book.Title || "Unknown Title"
                        }</h3>
                        <p class="bookAuthors">${
                          book.authors
                            ? book.authors.join(", ")
                            : "Unknown Author"
                        }</p>
                        <img src="${
                          book.image || "placeholder.png"
                        }" alt="${book.Title} cover image"class="bookImg">
                        <p class="bookDesc">${
                          book.description || "No description available."
                        }</p>
                        <a href="${
                          book.infoLink || "#"
                        }" class="bookInfoLink" ${
                book.infoLink ? "" : "style='display:none;'"
              } target="_blank" rel="noopener noreferrer">Info Link</a>
                        <p class="bookCat">${
                          book.categories
                            ? book.categories.join(", ")
                            : "No categories listed."
                        }</p>
                    `;

              bookGrid.append(bookItem); // Append book item to the grid
            }
          });

          bookGrid.id = "bookGrid"; // Ensure bookGrid has correct ID
        })
        .catch((error) => console.error("Error:", error)); // Handle fetch errors
    });
});

// Event listener for search suggestions
document.addEventListener("DOMContentLoaded", () => {
  const searchBox = document.getElementById("searchBox");
  const dataList = document.getElementById("suggestions");

  searchBox.addEventListener("keyup", () => {
    const query = searchBox.value.trim().toLowerCase();
    dataList.innerHTML = ""; // Clear previous results

    if (query.length === 0) {
      dataList.style.display = "none"; // Hide dropdown if empty
      return;
    }

    // Filter books that match the input query
    const filteredBooks = bookTitles
      .filter((book) => book.toLowerCase().includes(query))
      .slice(0, 15); // Limit suggestions to 15

    // Display filtered results as dropdown options
    filteredBooks.forEach((title) => {
      let op = document.createElement("option");
      op.textContent = title;
      dataList.appendChild(op);
    });
  });
});

/**
 * Removes punctuation from a given string.
 *
 * @param {string} str - The string to process.
 * @returns {string} - The string without punctuation.
 */
function removePunctuation(str) {
  return str.replace(/[^\w\s]|_/g, ""); // Removes punctuation but keeps words and spaces
}

/**
 * Displays an error message to the user.
 *
 * @param {string} message - The error message to display.
 */
function displayError(message) {
  const errP = document.getElementById("errorMsg");
  errP.textContent = "Error: " + message;
}

/**
 * Removes any displayed error message.
 */
function removeErrorMessage() {
  const errP = document.getElementById("errorMsg");
  errP.textContent = "";
}