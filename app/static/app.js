const $ = id => document.getElementById(id);
const mode = () => document.querySelector("input[name=mode]:checked").value;

// The words on the page that change with the mode
const WORDS = {
  quiz: { button: "Make quiz", count: "Number of questions", working: "Making your quiz..." },
  flashcards: { button: "Make flashcards", count: "Number of cards", working: "Making your flashcards..." },
};

function showMode() {
  $("go").textContent = WORDS[mode()].button;
  $("count-label").textContent = WORDS[mode()].count;
}

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

function showQuiz(questions) {
  questions.forEach((q, i) => {
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
  check.onclick = () => checkAnswers(questions, check);
  $("quiz").append(check);
}

function showCards(cards) {
  cards.forEach(c => {
    const card = document.createElement("button");
    card.className = "card";
    const inner = document.createElement("div");
    inner.className = "card-inner";
    const front = document.createElement("div");
    front.className = "card-face card-front";
    front.textContent = c.front;
    const back = document.createElement("div");
    back.className = "card-face card-back";
    back.textContent = c.back;
    inner.append(front, back);
    card.append(inner);

    // Screen readers only read the side that is showing
    const flip = flipped => {
      card.classList.toggle("flipped", flipped);
      front.setAttribute("aria-hidden", flipped);
      back.setAttribute("aria-hidden", !flipped);
    };
    flip(false);
    card.onclick = () => flip(!card.classList.contains("flipped"));
    $("cards").append(card);
  });
}

async function make() {
  const chosenMode = mode();
  $("status").textContent = WORDS[chosenMode].working;
  $("score").textContent = "";
  $("quiz").innerHTML = "";
  $("cards").innerHTML = "";
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
      form.append("mode", chosenMode);
      res = await fetch("/upload", { method: "POST", body: form });
    } else {
      res = await fetch("/quiz", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: $("text").value, count: Number(count), difficulty, mode: chosenMode }),
      });
    }
  } catch {
    $("status").textContent = "Could not reach the server.";
    return;
  }

  // A host's proxy can answer with an HTML error page instead of JSON (for example on a timeout)
  const data = await res.json().catch(() => null);
  if (!res.ok || !data) {
    $("status").textContent = typeof data?.detail === "string"
      ? data.detail
      : "Something went wrong, please try again in a minute.";
    return;
  }

  $("status").textContent = "";
  if (chosenMode === "flashcards") showCards(data.cards);
  else showQuiz(data.questions);
}

document.querySelectorAll("input[name=mode]").forEach(r => r.onchange = showMode);
showMode();  // browsers can remember the last choice after a refresh, so match the words to it

// Disable the button while working, so double clicks don't use up the quota
$("go").onclick = async () => {
  $("go").disabled = true;
  try {
    await make();
  } finally {
    $("go").disabled = false;
  }
};