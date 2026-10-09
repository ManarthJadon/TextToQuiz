const $ = id => document.getElementById(id);

function checkAnswers(questions, button) {
  let score = 0;
  questions.forEach((q, i) => {
    const div = $("quiz").children[i];
    const labels = div.querySelectorAll("label");
    const chosen = div.querySelector("input:checked");
    const picked = chosen ? Number(chosen.value) : -1;

    if (picked === q.answer_index) score++;
    labels[q.answer_index].classList.add("correct");
    if (picked !== -1 && picked !== q.answer_index) labels[picked].classList.add("wrong");
    div.querySelectorAll("input").forEach(r => r.disabled = true);

    const why = document.createElement("p");
    why.textContent = q.explanation;
    div.append(why);
  });
  $("score").textContent = `You got ${score} of ${questions.length}`;
  button.disabled = true;
}

$("go").onclick = async () => {
  $("status").textContent = "Making your quiz...";
  $("score").textContent = "";
  $("quiz").innerHTML = "";
  const file = $("file").files[0];
  const count = $("count").value;
  const difficulty = $("difficulty").value;

  let res;
  try {
    if (file) {
      const form = new FormData();
      form.append("file", file);
      form.append("count", count);
      form.append("difficulty", difficulty);
      res = await fetch("/upload", { method: "POST", body: form });
    } else {
      res = await fetch("/quiz", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: $("text").value, count: Number(count), difficulty }),
      });
    }
  } catch {
    $("status").textContent = "Could not reach the server.";
    return;
  }

  const data = await res.json();
  if (!res.ok) {
    $("status").textContent = typeof data.detail === "string" ? data.detail : "Something went wrong.";
    return;
  }

  $("status").textContent = "";
  data.questions.forEach((q, i) => {
    const div = document.createElement("div");
    div.className = "q";
    const title = document.createElement("strong");
    title.textContent = `${i + 1}. ${q.question}`;
    div.append(title);
    q.options.forEach((opt, j) => {
      const label = document.createElement("label");
      const radio = document.createElement("input");
      radio.type = "radio";
      radio.name = "q" + i;
      radio.value = j;
      label.append(radio, " " + opt);
      div.append(label);
    });
    $("quiz").append(div);
  });

  const check = document.createElement("button");
  check.textContent = "Check answers";
  check.onclick = () => checkAnswers(data.questions, check);
  $("quiz").append(check);
};