import { createFileRoute } from '@tanstack/react-router'
import {
  Activity,
  ArrowUp,
  Bot,
  CircleDot,
  Command,
  Send,
  Sparkles,
  Upload,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import { toast } from 'react-hot-toast'

export const Route = createFileRoute('/CommandsSection')({
  component: RouteComponent,
  validateSearch: (search) => ({ userId: Number(search.userId) }),
})

function RouteComponent() {
  const { userId } = Route.useSearch()

  const [command, setCommand] = useState('')
  const [taskId, setTaskId] = useState(-1)
  const [taskStatus, setTaskStatus] = useState(['PENDING TASK'])
  const [isSending, setIsSending] = useState(false)

  const [answerText, setAnswerText] = useState('')
  const [isSubmittingAnswer, setIsSubmittingAnswer] = useState(false)

  const [pendingFile, setPendingFile] = useState<File | null>(null)
  const [isUploadingAnswer, setIsUploadingAnswer] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!command.trim() || isSending) return
    setIsSending(true)
    setTaskStatus((prev) => [...prev, 'Sending task to your browser agent...'])
    try {
      const res = await fetch('http://127.0.0.1:8000/commands/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          command: command,
        }),
      })
      if (!res.ok) throw Error('Unable to post the command to server')
      const data = await res.json()
      setTaskId(data.task_id)
      setCommand('')
    } catch (error) {
      console.error(error)
      setTaskStatus((prev) => [...prev, 'Unable to send task. Please try again.'])
    } finally {
      setIsSending(false)
    }
  }

  useEffect(() => {
    if (taskId === -1) return
    const ws = new WebSocket(`ws://127.0.0.1:8000/commands/ws/${taskId}`)
    ws.onmessage = (event) => setTaskStatus((prev) => [...prev, event.data])
    ws.onerror = (err) => {
      console.error('WebSocket error:', err)
      setTaskStatus((prev) => [...prev, 'Live connection encountered an error.'])
    }
    return () => ws.close()
  }, [taskId])

  const lastEntry = taskStatus[taskStatus.length - 1] ?? ''

  const isAskingText = lastEntry.startsWith('ASKING_USER::')

  const askTextQuestion = isAskingText
    ? lastEntry.replace('ASKING_USER::', '')
    : null

  const isConfirmingEmail = lastEntry.startsWith('CONFIRM_SEND::')
  const emailDetails = isConfirmingEmail ? lastEntry.replace('CONFIRM_SEND::','') : null
  const details = emailDetails ? emailDetails.split('|||') : []
  

  const isAskingFile = lastEntry.startsWith('ASKING_USER_FILE::')
  const [askFileQuestion, askFileDocType] = isAskingFile
    ? lastEntry.replace('ASKING_USER_FILE::', '').split('|||')
    : [null, null]

  const running =
    taskId !== -1 &&
    !/complete|done|error|failed/i.test(lastEntry) &&
    !isAskingText &&
    !isAskingFile

  const submitTextAnswer = async () => {
    if (!answerText.trim() || taskId === -1) return
    setIsSubmittingAnswer(true)
    try {
      const res = await fetch(`http://127.0.0.1:8000/commands/${taskId}/answer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answer: answerText }),
      })
      if (!res.ok) throw new Error('Could not send answer')
      setAnswerText('')
    } catch (err) {
      console.error(err)
      toast.error('Could not send your answer. Please try again.')
    } finally {
      setIsSubmittingAnswer(false)
    }
  }

  const submitEmailAnswer = async(userAns: 'approved' | 'rejected') => {

    if(taskId == -1){
      return
    }
    try{
      const res = await fetch(`http://127.0.0.1:8000/commands/${taskId}/answer`, {
        method: 'POST',
        headers: {'Content-type': 'application/json'},
        body: JSON.stringify({answer:userAns}),
      })

      if (!res.ok){
        throw new Error('Could not send the respose')
        
      }
      toast.success('Response Sent to the AI')
    } catch (err) {
    console.error(err)
    toast.error('Could not send your decision. Please try again.')
  }
    


  }
  const submitFileAnswer = async () => {
    if (!pendingFile || !askFileDocType || taskId === -1) return
    setIsUploadingAnswer(true)
    const formData = new FormData()
    formData.append('doc_type', askFileDocType)
    formData.append('file', pendingFile)

    try {
      const res = await fetch(`http://127.0.0.1:8000/documents/${taskId}/answer/file`, {
        method: 'POST',
        body: formData,
      })
      if (!res.ok) throw new Error('Upload failed')
      setPendingFile(null)
    } catch (err) {
      console.error(err)
      toast.error('Could not send the file. Please try again.')
    } finally {
      setIsUploadingAnswer(false)
    }
  }

  return (
    <div className="mx-auto max-w-4xl pb-10 pt-4 sm:pt-10">
      <div className="mb-8">
        <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-indigo-400/15 bg-indigo-500/[0.08] px-3 py-1.5 text-xs font-medium text-indigo-200">
          <Sparkles className="h-3.5 w-3.5" /> Autonomous browser workspace
        </div>
        <h1 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">
          What can I take care of?
        </h1>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-zinc-400">
          Give your browser assistant a clear, natural-language task. Follow its
          progress in real time.
        </p>
      </div>

      <section className="overflow-hidden rounded-3xl border border-white/[0.08] bg-zinc-900/55 shadow-2xl shadow-black/20 backdrop-blur-sm">
        <form onSubmit={handleSubmit} className="p-4 sm:p-5">
          <div className="flex gap-3 rounded-2xl border border-white/[0.09] bg-zinc-950/70 p-2 transition focus-within:border-indigo-400/70 focus-within:ring-4 focus-within:ring-indigo-500/10">
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-indigo-500/10 text-indigo-300">
              <Bot className="h-5 w-5" />
            </span>
            <input
              value={command}
              onChange={(e) => setCommand(e.target.value)}
              id="command-input"
              className="min-w-0 flex-1 bg-transparent px-1 text-sm text-zinc-100 outline-none placeholder:text-zinc-600"
              placeholder="Ask Nexus to research, navigate, summarize, or automate..."
            />
            <button
              type="submit"
              disabled={!command.trim() || isSending}
              className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-indigo-500 text-white shadow-lg shadow-indigo-950/50 transition hover:bg-indigo-400 disabled:cursor-not-allowed disabled:opacity-40"
              aria-label="Send command"
            >
              {isSending ? (
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
              ) : (
                <ArrowUp className="h-4 w-4" />
              )}
            </button>
          </div>
        </form>
        <div className="border-t border-white/[0.07] px-5 py-3 text-xs text-zinc-500">
          <span className="font-medium text-zinc-400">Try:</span> Find the top
          three React testing libraries and compare them.
        </div>
      </section>

      <section className="mt-6 overflow-hidden rounded-3xl border border-white/[0.08] bg-zinc-900/45">
        <div className="flex items-center justify-between border-b border-white/[0.07] px-5 py-4">
          <div className="flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-zinc-800 text-zinc-300">
              <Activity className="h-4 w-4" />
            </span>
            <div>
              <h2 className="text-sm font-medium text-zinc-100">
                Live activity
              </h2>
              <p className="mt-0.5 text-xs text-zinc-500">
                Browser agent status
              </p>
            </div>
          </div>
          <span
            className={`flex items-center gap-2 rounded-full px-2.5 py-1 text-xs ${running ? 'bg-amber-400/10 text-amber-200' : 'bg-emerald-400/10 text-emerald-300'}`}
          >
            <CircleDot className="h-3.5 w-3.5" />
            {running ? 'Working' : 'Standing by'}
          </span>
        </div>

        <div className="min-h-36 p-5">
          <div className="flex gap-3">
            <span
              className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${running ? 'animate-pulse bg-amber-400' : 'bg-emerald-400'}`}
            />
            <div className="text-sm leading-6 text-zinc-300">
              {taskStatus.map((status, i) => (
                <div key={i}>
                  {status.startsWith('ASKING_USER::')
                    ? `Agent: ${status.replace('ASKING_USER::', '')}`
                    : status.startsWith('ASKING_USER_FILE::')
                      ? `Agent: ${status.replace('ASKING_USER_FILE::', '').split('|||')[0]}`
                      : status}
                </div>
              ))}
            </div>
          </div>

          {taskId === -1 && (
            <p className="mt-5 border-l border-zinc-700 pl-4 text-xs leading-5 text-zinc-500">
              Your assistant will report browser activity here once you send a
              task.
            </p>
          )}

          {isAskingText && (
            <div className="mt-5 flex items-center gap-2 rounded-2xl border border-indigo-400/20 bg-indigo-500/[0.06] p-2">
              <input
                value={answerText}
                onChange={(e) => setAnswerText(e.target.value)}
                placeholder={askTextQuestion ?? 'Type your answer...'}
                className="min-w-0 flex-1 bg-transparent px-2 text-sm text-zinc-100 outline-none placeholder:text-zinc-500"
              />
              <button
                onClick={submitTextAnswer}
                disabled={!answerText.trim() || isSubmittingAnswer}
                className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-indigo-500 text-white transition hover:bg-indigo-400 disabled:cursor-not-allowed disabled:opacity-40"
                aria-label="Send answer"
              >
                {isSubmittingAnswer ? (
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </button>
            </div>
          )}

          {isAskingFile && (
            <div className="mt-5 flex items-center gap-2 rounded-2xl border border-indigo-400/20 bg-indigo-500/[0.06] p-3">
              <input
                type="file"
                accept="application/pdf"
                onChange={(e) => setPendingFile(e.target.files?.[0] ?? null)}
                className="min-w-0 flex-1 text-xs text-zinc-300"
              />
              <button
                onClick={submitFileAnswer}
                disabled={!pendingFile || isUploadingAnswer}
                className="inline-flex h-9 items-center gap-2 rounded-xl bg-indigo-500 px-3 text-xs font-medium text-white transition hover:bg-indigo-400 disabled:cursor-not-allowed disabled:opacity-40"
              >
                {isUploadingAnswer ? (
                  <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                ) : (
                  <Upload className="h-3.5 w-3.5" />
                )}
                {isUploadingAnswer ? 'Uploading...' : 'Send file'}
              </button>
            </div>
          )}

          {isConfirmingEmail && (
            <div>
              <div>Are you sure you want to send the email with the following details:-</div>
              {
                details.map( (det,i) => 
                (<div key = {i}>{i === 0 ? <div>to: {det}</div> :  (i === 1 ? <div>Subject : {det}</div> : <div>Body : {det}</div>)}</div>)
                )
              }

              <div className="mt-3 flex gap-2">
              <button onClick={() => submitEmailAnswer('approved')}>Send</button>
              <button onClick={() => submitEmailAnswer('rejected')}>Cancel</button>
            </div>
            </div>
          )
        }
        </div>
      </section>

      <div className="mt-5 flex items-center gap-3 px-1 text-xs text-zinc-600">
        <Command className="h-4 w-4" /> Nexus works in your connected browser
        session.
      </div>
    </div>
  )
}