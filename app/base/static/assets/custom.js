document.addEventListener("DOMContentLoaded", function(event) {
  loader_dom = document.getElementsByClassName("loader")[0];
  loader_dom.style.display="none";
  const preview = document.querySelector('.container-audio');
  let submit_btn=document.getElementsByClassName("submit-btn")[0];
  submit_btn.addEventListener('click', e => {
      loader_dom.style.display="block";
      MIDIjs.stop();
      content = document.getElementsByClassName("text-field")[0].value;
      composer = document.getElementsByClassName("select-field")[0].value;
      let json_data = {'data-uri': content, 'composer': composer }
  
      // this is ajax part when it send the json data of the image from the 
      // webcame to our flask back end at /predict using POST method 
      console.log("Sending info to python endpoint!")
      fetch('/predict/', {
        method: 'POST',
        processData: false,
        headers: {
          'Accept': 'application/json, text/plain, */*',
          'Content-Type': 'application/json; charset=utf-8'
        },
        body: JSON.stringify(json_data)
      }).then(res=>res.json())
        .then(data => {
          loader_dom.style.display="none";
          // this is when we successfully receive the data back from the flask backend
          console.log(data);
          // MIDIjs.play(data.audio_filename);
          // const audio = document.createElement('audio');
          // audio.controls = true;
          // audio.loop = true;
          // audio.autoplay = true;

          // const source = document.createElement('source')
          // source.src = data.audio_filename
          // source.type = "audio/ogg"
          // audio.appendChild(source);
          // console.log(data.audio_filename) 

          const audio = document.createElement('midi-player');
          audio.src = data.audio_filename;
          audio.setAttribute("sound-font",'');
          preview.setAttribute("class",'d-flex justify-content-center');
          preview.appendChild(audio);

        });
  });


  var a = new AudioSynthView();
  a.draw();
});

