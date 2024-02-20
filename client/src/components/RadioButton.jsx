function RadioButton(props) {
  const select_job_title = () => {
    return props.select(props.sendTitle);
  };

  console.log(props.key);

  return (
    <div className="radio_button">
      <label>
        <input type="radio" name="job" onClick={select_job_title} />
        {props.sendTitle}
      </label>
    </div>
  );
}

export default RadioButton;
