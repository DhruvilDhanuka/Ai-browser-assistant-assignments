import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useMutation } from '@tanstack/react-query'
import {
  ArrowLeft,
  CheckCircle2,
  FileText,
  ShieldCheck,
  Upload,
  X,
} from 'lucide-react'
import { useRef, useState } from 'react'
import { toast } from 'react-hot-toast'

export const Route = createFileRoute('/resume_upload')({
  component: RouteComponent,
  validateSearch: (search) => ({ userId: Number(search.userId) }),
})

type UploadDocsInput = { userId: number; file: File }

async function uploadDocs({ userId, file }: UploadDocsInput) {
  const formData = new FormData()
  formData.append('doc_type', 'resume')
  formData.append('file', file)
  const res = await fetch(`http://localhost:8000/documents/${userId}`, {
    method: 'POST',
    body: formData,
  })
  if (!res.ok) throw Error('Invalid Upload')
}

function RouteComponent() {
  const { userId } = Route.useSearch()
  const navigate = useNavigate()
  const inputRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const { mutate, isPending } = useMutation({
    mutationFn: uploadDocs,
    onSuccess: () => {
      toast.success('Résumé uploaded successfully')
      navigate({ to: '/CommandsSection' ,search: { userId }})
    },
    onError: () => toast.error('Your résumé could not be uploaded'),
  })
  const clearFile = () => {
    setFile(null)
    if (inputRef.current) inputRef.current.value = ''
  }

  return (
    <div className="mx-auto max-w-2xl pb-10 pt-4 sm:pt-10">
      <button
        type="button"
        onClick={() => navigate({ to: '/' })}
        className="mb-8 inline-flex items-center gap-2 text-sm text-zinc-500 transition hover:text-zinc-200"
      >
        <ArrowLeft className="h-4 w-4" /> Back to profile
      </button>
      <div className="mb-8">
        <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl border border-indigo-400/20 bg-indigo-500/10">
          <FileText className="h-5 w-5 text-indigo-300" />
        </div>
        <h1 className="text-3xl font-semibold tracking-tight text-white">
          Add your résumé
        </h1>
        <p className="mt-3 text-sm leading-6 text-zinc-400">
          Upload your latest résumé so Nexus can better understand your
          background before it starts working.
        </p>
      </div>
      <section className="rounded-3xl border border-white/[0.08] bg-zinc-900/55 p-5 shadow-2xl shadow-black/20 backdrop-blur-sm sm:p-7">
        <input
          ref={inputRef}
          id="resume-file"
          type="file"
          accept="application/pdf"
          className="sr-only"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
        {!file ? (
          <label
            htmlFor="resume-file"
            className="group flex min-h-64 cursor-pointer flex-col items-center justify-center rounded-2xl border border-dashed border-zinc-700 bg-zinc-950/40 px-6 text-center transition hover:border-indigo-400/60 hover:bg-indigo-500/[0.04]"
          >
            <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-zinc-800 text-zinc-400 transition group-hover:scale-105 group-hover:bg-indigo-500/15 group-hover:text-indigo-300">
              <Upload className="h-5 w-5" />
            </span>
            <span className="mt-4 text-sm font-medium text-zinc-200">
              Drop your PDF here, or browse files
            </span>
            <span className="mt-2 text-xs text-zinc-500">PDF format only</span>
          </label>
        ) : (
          <div className="rounded-2xl border border-indigo-400/20 bg-indigo-500/[0.06] p-4">
            <div className="flex items-center gap-3">
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-rose-500/10 text-rose-300">
                <FileText className="h-5 w-5" />
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-zinc-100">
                  {file.name}
                </p>
                <p className="mt-1 text-xs text-zinc-500">
                  {(file.size / 1024 / 1024).toFixed(2)} MB · PDF document
                </p>
              </div>
              <button
                type="button"
                onClick={clearFile}
                className="rounded-lg p-2 text-zinc-500 transition hover:bg-white/[0.07] hover:text-zinc-200"
                aria-label="Remove selected file"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}
        <div className="mt-6 flex flex-col-reverse gap-4 border-t border-white/[0.07] pt-5 sm:flex-row sm:items-center sm:justify-between">
          <span className="flex items-center gap-2 text-xs text-zinc-500">
            <ShieldCheck className="h-4 w-4 text-emerald-400" /> Encrypted and
            handled securely
          </span>
          <button
            disabled={!file || isPending}
            onClick={() => file && mutate({ userId, file })}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-indigo-500 to-violet-500 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-950/50 transition hover:from-indigo-400 hover:to-violet-400 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isPending ? (
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
            ) : (
              <Upload className="h-4 w-4" />
            )}
            {isPending ? 'Uploading…' : 'Upload résumé'}
          </button>
        </div>
      </section>
      <div className="mt-5 flex items-center gap-3 rounded-2xl border border-white/[0.06] bg-zinc-900/30 px-4 py-3 text-xs text-zinc-500">
        <CheckCircle2 className="h-4 w-4 shrink-0 text-indigo-300" /> Your
        résumé is used only to personalize your assistant workspace.
      </div>
    </div>
  )
}
