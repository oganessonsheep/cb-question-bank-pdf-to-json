#!/usr/bin/env python3
import json
import argparse
import sys
import fitz


def extract_sat_data(file_path, output_path):
    try:
        doc = fitz.open(file_path)
        blocks = []
        raw_questions = []
        for page in doc:
            for block in page.get_text("blocks", sort=True):
                blocks.append(block)
                if "Question Difficulty" in block[4]:
                    raw_questions.append(blocks)
                    blocks = []
    except Exception as e:
        print("Exception in pdf-to-text: ", e)
        sys.exit(1)

    questions = []
    for blocks in raw_questions:
        metadata = {}
        metadata["Assessment"] = blocks[6][4].replace("\n", " ").strip()
        metadata["Test"] = blocks[7][4].replace("\n", " ").strip()
        metadata["Domain"] = blocks[8][4].replace("\n", " ").strip()
        metadata["Skill"] = blocks[9][4].replace("\n", " ").strip()
        metadata["Difficulty"] = blocks[-1][4].split("\n")[-2]
        q_id = blocks[0][4][-9:-1]
        body = ""
        choices = {}
        correct_ans = ""
        reason = ""

        j = 0

        body_chunks = []
        current_para = []

        PARA_GAP = 10

        last_bottom = None

        for i in range(11, len(blocks)):
            if blocks[i][4][:3] == "A. ":
                j = i
                break
            text = blocks[i][4].replace("\n", " ").strip()
            y0 = blocks[i][1]
            y1 = blocks[i][3]

            if last_bottom is None:
                current_para.append(text)
            else:
                if y0 - last_bottom > PARA_GAP:
                    body_chunks.append(" ".join(current_para))
                    current_para = [text]
                else:
                    current_para.append(text)

            last_bottom = y1

        if current_para:
            body_chunks.append(" ".join(current_para))

        body = "\n\n".join(body_chunks)

        current_choice = None
        for i in range(j, len(blocks)):
            text = blocks[i][4]
            if text.startswith("ID: ") and "Answer" in text:
                j = i
                break

            if text[:3] in ("A. ", "B. ", "C. ", "D. "):
                current_choice = text[0]
                choices[current_choice] = text[3:].replace("\n", " ")
            elif current_choice:
                choices[current_choice] += text.replace("\n", " ")

        for key in choices:
            choices[key] = choices[key].strip()

        for i in range(j, len(blocks)):
            if "Correct Answer:" in blocks[i][4]:
                j = i
                lines = blocks[i][4].strip().split("\n")
                if len(lines) > 1:
                    correct_ans = lines[1].strip()
                break

        reason_active = False
        for i in range(j, len(blocks)):
            text = blocks[i][4]
            if text.startswith("Question Difficulty:"):
                j = i
                break
            if reason_active:
                reason += text.replace("\n", " ")
                if reason[-1] == " ":
                    reason = reason[:-1] + "\n\n"
            if text.startswith("Rationale"):
                reason_active = True

        reason = reason.strip()

        questions.append(
            {
                "question_id": q_id,
                "metadata": metadata,
                "body": body,
                "choices": choices,
                "correct_answer": correct_ans,
                "reason": reason,
            }
        )

    # for question in questions:
    #     print(question['question_id'], '\n')
    #     print(question['metadata'], '\n')
    #     print(question['body'], '\n')
    #     for c, tx in question['choices'].items(): print(c, tx, '\n')
    #     print(question['correct_answer'], '\n')
    #     print(question['reason'], '\n')
    #     print('\n\n')

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract SAT questions from text file to JSON."
    )
    parser.add_argument("input", help="Path to input text file.")
    parser.add_argument(
        "output",
        nargs="?",
        default="output.json",
        help="Path to output JSON file."
    )
    args = parser.parse_args()
    extract_sat_data(args.input, args.output)
