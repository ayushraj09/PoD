# Fraud test report

Run 2026-10-30 12:48 on waitlist `fraud-lab` (product: Acne face wash for oily skin: clears pimples in two weeks without drying the skin.)

**40 caught / correct, 1 missed, 3 measured (known limits).**

| Group | Attack | Expected | Result | Got |
|---|---|---|---|---|
| baseline | **genuine, specific (Tara)**: real story with moment, cost, frequency | verified, high pain, no flags | ✅ | verified trust=100 pain=85 flags=[] |
| baseline | **genuine, different person (Moira)**: different voice, different story | verified, no same_voice | ✅ | verified trust=100 pain=85 flags=[] similarity_to_A=0.162 |
| baseline | **genuine but vague (Rishi)**: real problem, no specifics | verified, medium pain 40-69 | ✅ | verified trust=100 pain=45 flags=[] |
| baseline | **genuine Hindi (Lekha)**: specific story in Hindi | verified, Devanagari transcript | ✅ | verified trust=100 pain=85 flags=[] |
| identity | **same voice x4, new device+network each**: one person, 4 emails, different stories | #2-#4 same_voice; all ring_member; #2-#4 not verified | ✅ | verdicts=['suspicious', 'fake', 'fake', 'fake'] flags=[['ring_member'], ['ring_member', 'same_voice'], ['ring_member', 'same_voice'], ['ring_member', 'same_voice']] sims=[0.893, 0.888, 0.899] |
| identity | **exact replay of a genuine recording**: re-upload priya's file with a new email | same_voice + same_answer, not verified | ✅ | fake trust=15 pain=85 flags=['same_answer', 'same_voice'] similarity=1.0 |
| identity | **modified replay: pitch +2 semitones**: voice changer: higher pitch | same_voice (ideal) — measured | ✅ | fake trust=0 pain=85 flags=['same_answer', 'same_voice', 'ring_member'] similarity=0.602 |
| identity | **modified replay: pitch -2 semitones**: voice changer: lower pitch | same_voice (ideal) — measured | ➖ | suspicious trust=65 pain=85 flags=['same_answer'] similarity=0.574 |
| identity | **modified replay: speed 1.15x**: sped-up replay | same_voice (ideal) — measured | ✅ | fake trust=0 pain=85 flags=['same_answer', 'same_voice', 'ring_member'] similarity=0.965 |
| identity | **modified replay: phone line 8 kHz**: replayed over a phone call | same_voice (ideal) — measured | ✅ | fake trust=0 pain=90 flags=['same_answer', 'same_voice', 'ring_member'] similarity=0.737 |
| identity | **replay with background noise**: noise added to hide the copy | same_voice | ✅ | fake trust=0 pain=85 flags=['same_answer', 'same_voice', 'ring_member'] similarity=0.959 |
| content | **copied script, different voice**: click farm reads priya's exact answer | same_answer, not verified | ❌ | verified trust=100 pain=85 flags=[] |
| content | **paraphrased script**: same story, reworded | same_answer (ideal) — measured | ➖ | verified trust=100 pain=100 flags=[] |
| content | **prompt injection, direct**: talks to the AI to raise the score | pain <= 5 | ✅ | verified trust=100 pain=0 flags=[] |
| content | **prompt injection, polite**: talks to the AI to raise the score | pain <= 5 | ✅ | verified trust=100 pain=2 flags=[] |
| content | **prompt injection, Hinglish**: talks to the AI to raise the score | pain <= 5 | ✅ | suspicious trust=50 pain=0 flags=['same_voice'] |
| content | **keyword stuffing**: high score without a real problem | pain <= 69 | ✅ | verified trust=100 pain=5 flags=[] |
| content | **specific but off-topic**: high score without a real problem | pain <= 69 | ✅ | verified trust=100 pain=5 flags=[] |
| content | **generic enthusiasm**: high score without a real problem | pain <= 39 | ✅ | verified trust=100 pain=5 flags=[] |
| audio | **raw TTS file (no mic, no codec)**: AI voice uploaded directly | possible_ai_voice (ideal) — measured | ➖ | verified trust=100 pain=85 flags=[] |
| audio | **virtual mic with digital silence gaps**: audio injected into a fake microphone | possible_ai_voice | ✅ | fake trust=20 pain=78 flags=['possible_ai_voice', 'same_voice'] |
| audio | **non-speech sound (beeping)**: audio that isn't a person talking | not verified | ✅ | suspicious trust=60 pain=0 flags=['no_speech'] |
| audio | **background noise only**: recording with nobody speaking | no_speech, not verified | ✅ | suspicious trust=60 pain=0 flags=['no_speech'] |
| audio | **1.5 s answer**: too short to judge | too_short, not verified | ✅ | fake trust=0 pain=5 flags=['too_short', 'same_voice', 'ring_member'] |
| network | **same device, 2 emails, different voices**: one phone, two accounts | #2 repeat_device | ✅ | flags=[['same_answer'], ['repeat_device', 'same_answer']] |
| network | **same network, 3 signups**: one wifi, many signups | #3 repeat_ip | ✅ | flags=[['ring_member', 'same_answer', 'same_voice'], ['same_answer', 'same_voice'], ['repeat_ip', 'same_answer', 'same_voice']] |
| email | **throwaway domain mailinator.com**: disposable inbox | disposable_email | ✅ | True |
| email | **throwaway domain sub.mailinator.com**: disposable inbox | disposable_email | ✅ | True |
| email | **throwaway domain guerrillamail.com**: disposable inbox | disposable_email | ✅ | True |
| email | **throwaway domain yopmail.com**: disposable inbox | disposable_email | ✅ | True |
| email | **throwaway domain 10minutemail.com**: disposable inbox | disposable_email | ✅ | True |
| email | **throwaway domain temp-mail.org**: disposable inbox | disposable_email | ✅ | True |
| email | **throwaway domain sharklasers.com**: disposable inbox | disposable_email | ✅ | True |
| email | **first signup (control)**: plain gmail address | 201 | ✅ | 201 |
| email | **alias ravikumar.78c68@gmail.com**: same inbox, new spelling | 409 same signup | ✅ | 409 already_signed_up |
| email | **alias ravi.kumar.78c68+2@gmail.com**: same inbox, new spelling | 409 same signup | ✅ | 409 already_signed_up |
| email | **alias RAVI.KUMAR.78c68@gmail.com**: same inbox, new spelling | 409 same signup | ✅ | 409 already_signed_up |
| email | **alias ravi.kumar.78c68@googlemail.com**: same inbox, new spelling | 409 same signup | ✅ | 409 already_signed_up |
| email | **alias r.a.v.i.kumar.78c68@gmail.com**: same inbox, new spelling | 409 same signup | ✅ | 409 already_signed_up |
| email | **plus alias on another provider**: +tag on outlook.com | 409 | ✅ | 201/409 already_signed_up |
| email | **made-up domain**: email that can't receive mail | 400 invalid_email | ✅ | 400 invalid_email |
| api | **oversized upload (3 MB+)**: huge file to waste resources | 400 bad_audio | ✅ | 400 bad_audio |
| api | **non-audio file type**: upload an executable | 400 bad_audio | ✅ | 400 bad_audio |
| api | **flood from one network**: bot signs up again and again | 429 after 10 per hour | ✅ | statuses=[201, 201, 201, 201, 201, 201, 201, 201, 429] |
