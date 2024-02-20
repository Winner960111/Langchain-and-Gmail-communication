const express = require("express");
const bodyParser = require("body-parser");
const path = require("path");
const cors = require("cors");
const multer = require("multer");
const fs = require("fs");
require("dotenv").config();
const app = express();

// Init Middleware
app.use(express.json());

// parse application/x-www-form-urlencoded
app.use(cors());
app.use(bodyParser.urlencoded({ extended: false }));
app.use(bodyParser.json());

let resumeName = "";

// Define Routes
app.post("/test", async (req, res) => {
  try {
    const jsonData = {
      title: req.body.title,
      job_description: req.body.job_description,
    };
    // Convert it to a JSON string
    const jsonString = JSON.stringify(jsonData, null, 2); // the 'null' and '2' arguments add indentation for readability

    // Define the path for your JSON file
    const filePath = `./job_description/${req.body.title}.json`;

    // Write the JSON string to a file
    fs.writeFile(filePath, jsonString, "utf8", (err) => {
      if (err) {
        console.error("An error occurred while writing JSON Object to File.");
        return console.error(err);
      }
      res.send({
        confirm: "success",
      });
      console.log("JSON file has been saved.");
    });
  } catch (e) {
    console.log(e);
  }
});

//create the json file of candidate info
app.post("/test/candidateInfo", async (req, res) => {
  try {
    const candidate_data = {
      first_name: req.body.first_name,
      last_name: req.body.last_name,
      email: req.body.email,
      phone: req.body.phone,
    };
    const candidate_json =
      req.body.first_name + " " + req.body.last_name + "_" + req.body.phone;
    resumeName = candidate_json;

    // Convert it to a JSON string
    const candidate_jsonString = JSON.stringify(candidate_data, null, 2); // the 'null' and '2' arguments add indentation for readability

    // Define the path for your JSON file
    const candidate_filePath = `./resume/${candidate_json}.json`;

    // Write the JSON string to a file
    fs.writeFile(candidate_filePath, candidate_jsonString, "utf8", (err) => {
      if (err) {
        console.error("An error occurred while writing JSON Object to File.");
        return console.error(err);
      }
      res.send({
        confirm: "success",
      });
      console.log("JSON file has been saved.");
    });
  } catch (e) {
    console.log(e);
  }
});

// Configure storage for Multer
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, "./resume/"); // Specify the directory where files will be saved
  },
  filename: (req, file, cb) => {
    cb(null, `${resumeName}.pdf`);
  },
});

// Initialize Multer with the storage configuration
const upload = multer({ storage: storage });

// Endpoint to handle file uploads
app.post("/test/upload", upload.single("file"), (req, res) => {
  if (!req.file) {
    return res.status(400).send("No file was uploaded.");
  }

  // Access the file object via req.file
  console.log(req.file);

  // Do something with the uploaded file here
  // ...

  res.send("File uploaded successfully!");
});

// Serve static assets in production
if (process.env.NODE_ENV === "production") {
  console.log("PRODUCTION => ");
  // Set static folder
  app.use(express.static("client/dist"));

  app.get("*", (req, res) => {
    res.sendFile(path.resolve(__dirname, "client", "dist", "index.html"));
  });
}

const PORT = process.env.PORT || 5050;

const server = app.listen(PORT, async () => {
  console.log(`Server started on ${PORT}`);
});
