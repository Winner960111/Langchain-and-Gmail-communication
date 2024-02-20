import "./App.css";
import RadioButton from "./components/RadioButton";
import axios from "axios";
import { useEffect, useState } from "react";
function App() {
  const [selectJob, setSelectJob] = useState("");
  const [jobDescription, setjobDescription] = useState("");
  const [jobTitle, setjobTitle] = useState("");
  const [jobs, setJobs] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);

  useEffect(() => {
    console.log("job status =>", jobs);
  }, [jobs]);
  // create new job_description
  const submit_description = () => {
    setJobs([...jobs, jobTitle]);

    const data = {
      title: jobTitle,
      job_description: jobDescription,
    };

    //communication with backend
    axios
      .post("http://localhost:5050/test", data)
      .then((res) => console.log(res.data.confirm))
      .catch(() => console.log("error"));

    //initialize job_window
    setjobDescription("");
    setjobTitle("");
  };

  const handleUpload = async (event) => {
    event.preventDefault();

    if (selectedFile) {
      const formData = new FormData();
      formData.append("file", selectedFile);

      try {
        const response = await axios.post(
          "http://localhost:5050/test/upload",
          formData,
          {
            headers: {
              "Content-Type": "multipart/form-data",
            },
          }
        );

        // Handle the response from the server
        console.log(response.data);
      } catch (error) {
        // Handle any errors here
        console.error("File upload error:", error);
      }
    }
  };

  //candidate info
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");

  const [candidates, setCandidates] = useState([]);
  //candidate submit into backend
  const submit_candidate = () => {
    const candidate_data = {
      first_name: firstName,
      last_name: lastName,
      email: email,
      phone: phone,
    };

    setCandidates((prev) => [
      ...prev,
      { ...candidate_data, checked: false, id: candidates.length },
    ]);

    //communication with backend
    axios
      .post("http://localhost:5050/test/candidateInfo", candidate_data)
      .then((res) => console.log(res.data.confirm))
      .catch(() => console.log("error"));

    setFirstName("");
    setLastName("");
    setEmail("");
    setPhone("");
  };

  //send selected candidates and Job title to backend
  const sendToBot = async () => {
    console.log(
      "selected candidates = >",
      candidates.filter((candidate) => candidate.checked === true)
    );

    const sendData = {
      job_description_title: selectJob,
      candidates: candidates.filter((candidate) => candidate.checked === true),
    };
    const config = {
      headers: {
        "Content-Type": "application/json",
      },
    };

    console.log("selected Data = >", sendData);

    const url = "http://localhost:5000/screen_start";

    await axios
      .post(url, JSON.stringify(sendData), config)
      .then((res) => console.log(res))
      .catch((res) => console.log(res));
  };

  const handleCheckboxClick = (candidate) => {
    setCandidates(
      candidates.map((item) =>
        candidate.id === item.id ? { ...item, checked: !item.checked } : item
      )
    );
  };

  return (
    <div className="App">
      <div className="input">
        <div className="job">
          <input
            value={jobTitle}
            className="job_title"
            type="text"
            placeholder="JOB TITLE"
            onChange={(e) => setjobTitle(e.target.value)}
          ></input>
          <textarea
            value={jobDescription}
            className="job_description"
            type="text"
            placeholder="Job Description"
            onChange={(e) => setjobDescription(e.target.value)}
          ></textarea>
          <button className="job_button" onClick={submit_description}>
            Submit
          </button>
        </div>
        <div className="candidate_main">
          <div className="candidate">
            <input
              value={firstName}
              type="text"
              placeholder="firstname"
              onChange={(e) => setFirstName(e.target.value)}
            ></input>
            <input
              value={lastName}
              type="text"
              placeholder="lastname"
              onChange={(e) => setLastName(e.target.value)}
            ></input>
            <input
              value={email}
              type="email"
              placeholder="email"
              onChange={(e) => setEmail(e.target.value)}
            ></input>
            <input
              value={phone}
              type="phone"
              placeholder="phone"
              onChange={(e) => setPhone(e.target.value)}
            ></input>
            <button className="candidate_button" onClick={submit_candidate}>
              Submit
            </button>
            <div className="file_upload">
              <input
                className="file"
                type="file"
                placeholder="file"
                onChange={(e) => setSelectedFile(e.target.files[0])}
              ></input>
              <button className="file_button" onClick={handleUpload}>
                Submit
              </button>
            </div>
          </div>

          <div className="main">
            <div className="main_contents">
              <div className="main_job">
                {jobs.length !== 0
                  ? jobs.map((item, id) => (
                      <RadioButton
                        key={id}
                        sendTitle={item}
                        select={setSelectJob}
                      />
                    ))
                  : null}
              </div>
              <div className="main_candidate">
                {candidates.map((candidate, index) => (
                  <label key={index}>
                    <input
                      type="checkbox"
                      value={candidate.checked}
                      onClick={() => handleCheckboxClick(candidate)}
                    />
                    {candidate.first_name + " " + candidate.last_name}
                  </label>
                ))}
              </div>
            </div>
            <button className="main_submit" onClick={sendToBot}>
              Submit
            </button>
            <button className="main_dialog">Dialog</button>
          </div>
        </div>
      </div>
      <div className="contents">
        <div className="description_show"></div>
        <div className="dialog_text"></div>
      </div>
    </div>
  );
}

export default App;
