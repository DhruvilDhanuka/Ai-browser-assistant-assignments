import { useForm } from '@tanstack/react-form'
import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useMutation } from '@tanstack/react-query'
import {
  CheckCircle2,
  ChevronRight,
  GraduationCap,
  Mail,
  Phone,
  Sparkles,
  UserRound,
  Wrench,
} from 'lucide-react'
import { useState } from 'react'
import { toast } from 'react-hot-toast'
import { z } from 'zod'
import type { AnyFieldApi } from '@tanstack/react-form'

export const Route = createFileRoute('/')({ component: Home })

const userInfoSchema = z.object({
  Name: z.string().min(1, 'Please fill a valid name'),
  Email: z.string().email('Please enter a valid email address'),
  Contact_number: z
    .string()
    .regex(/^\d+$/, 'Mobile number must contain only digits')
    .min(10, 'Please enter a valid phone number'),
  College: z.string().min(4, 'Please fill a valid College Name'),
  Skills: z.string().min(5, 'Please fill valid skills'),
})

type UserInfoPayload = z.infer<typeof userInfoSchema> & {
  extra_info: Record<string, unknown>
}

async function createUser(userInfo: UserInfoPayload) {
  const res = await fetch('http://localhost:8000/users', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(userInfo),
  })
  if (!res.ok) throw new Error(JSON.stringify(await res.json()))
  return res.json()
}

function FieldError({ field }: { field: AnyFieldApi }) {
  if (!field.state.meta.isTouched || !field.state.meta.errors.length)
    return null
  return (
    <p className="mt-1.5 text-xs text-rose-400">
      {field.state.meta.errors
        .map((error) => error?.message ?? error)
        .join(', ')}
    </p>
  )
}

const fieldClass =
  'w-full rounded-xl border border-white/[0.09] bg-zinc-950/70 px-4 py-3 text-sm text-zinc-100 outline-none placeholder:text-zinc-600 transition duration-200 hover:border-white/[0.15] focus:border-indigo-400/70 focus:ring-4 focus:ring-indigo-500/10'

function Home() {
  const navigate = useNavigate()
  const [userId, setUserId] = useState<number | null>(null)
  const { mutate, isPending } = useMutation({
    mutationFn: createUser,
    onSuccess: (data) => {
      setUserId(data.id)
      localStorage.setItem('user_id', String(data.id))
      toast.success('Profile saved successfully')
    },
    onError: (err) => {
      console.error('Failed to create user:', err)
      toast.error('Unable to save your profile')
    },
  })
  const form = useForm({
    defaultValues: {
      Name: '',
      Email: '',
      Contact_number: '',
      College: '',
      Skills: '',
    },
    onSubmit: async ({ value }) => mutate({ ...value, extra_info: {} }),
  })
  const fields = [
    {
      name: 'Name' as const,
      label: 'Full name',
      placeholder: 'Enter your name',
      icon: UserRound,
      type: 'text',
    },
    {
      name: 'Email' as const,
      label: 'Email address',
      placeholder: 'you@example.com',
      icon: Mail,
      type: 'email',
    },
    {
      name: 'Contact_number' as const,
      label: 'Phone number',
      placeholder: 'Enter your contact number',
      icon: Phone,
      type: 'tel',
    },
    {
      name: 'College' as const,
      label: 'College or university',
      placeholder: 'Enter your institution',
      icon: GraduationCap,
      type: 'text',
    },
    {
      name: 'Skills' as const,
      label: 'Skills',
      placeholder: 'e.g. React, Python, research',
      icon: Wrench,
      type: 'text',
    },
  ]

  return (
    <div className="mx-auto max-w-3xl pb-10 pt-4 sm:pt-10">
      <div className="mb-8 text-center sm:mb-10">
        <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-indigo-400/15 bg-indigo-500/[0.08] px-3 py-1.5 text-xs font-medium text-indigo-200">
          <Sparkles className="h-3.5 w-3.5" /> Your intelligent workspace
        </div>
        <h1 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">
          Let’s personalize your assistant.
        </h1>
        <p className="mx-auto mt-3 max-w-xl text-sm leading-6 text-zinc-400">
          A few details help Nexus tailor its browser tasks and recommendations
          to you.
        </p>
      </div>
      <section className="overflow-hidden rounded-3xl border border-white/[0.08] bg-zinc-900/55 shadow-2xl shadow-black/20 backdrop-blur-sm">
        <div className="flex items-center justify-between border-b border-white/[0.07] px-5 py-4 sm:px-7">
          <div>
            <h2 className="font-medium text-zinc-100">Profile details</h2>
            <p className="mt-1 text-xs text-zinc-500">
              All fields are used to set up your workspace.
            </p>
          </div>
          <span className="hidden items-center gap-1.5 text-xs text-zinc-500 sm:flex">
            <CheckCircle2 className="h-3.5 w-3.5 text-indigo-300" /> Secure
            setup
          </span>
        </div>
        <form
          onSubmit={(e) => {
            e.preventDefault()
            form.handleSubmit()
          }}
          className="p-5 sm:p-7"
        >
          <div className="grid gap-5 sm:grid-cols-2">
            {fields.map(({ name, label, placeholder, icon: Icon, type }) => (
              <form.Field
                key={name}
                name={name}
                validators={{ onBlur: userInfoSchema.shape[name] }}
              >
                {(field) => (
                  <div className={name === 'Skills' ? 'sm:col-span-2' : ''}>
                    <label
                      htmlFor={name}
                      className="mb-2 flex items-center gap-2 text-xs font-medium text-zinc-300"
                    >
                      <Icon className="h-3.5 w-3.5 text-zinc-500" />
                      {label}
                    </label>
                    <input
                      id={name}
                      type={type}
                      className={fieldClass}
                      value={field.state.value}
                      onChange={(e) => field.handleChange(e.target.value)}
                      onBlur={field.handleBlur}
                      placeholder={placeholder}
                    />
                    <FieldError field={field} />
                  </div>
                )}
              </form.Field>
            ))}
          </div>
          <div className="mt-8 flex flex-col-reverse gap-3 border-t border-white/[0.07] pt-5 sm:flex-row sm:justify-end">
            <button
              type="button"
              disabled={!userId}
              onClick={() =>
                userId && navigate({ to: '/resume_upload', search: { userId } })
              }
              className="inline-flex items-center justify-center gap-2 rounded-xl border border-white/[0.1] px-4 py-2.5 text-sm font-medium text-zinc-300 transition hover:border-white/[0.2] hover:bg-white/[0.05] hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
            >
              Upload résumé <ChevronRight className="h-4 w-4" />
            </button>
            <button
              type="submit"
              disabled={isPending}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-indigo-500 to-violet-500 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-950/50 transition hover:from-indigo-400 hover:to-violet-400 focus:outline-none focus:ring-4 focus:ring-indigo-500/25 disabled:cursor-wait disabled:opacity-70"
            >
              {isPending ? (
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
              ) : (
                <CheckCircle2 className="h-4 w-4" />
              )}
              {isPending ? 'Saving profile…' : 'Save details'}
            </button>
          </div>
        </form>
      </section>
    </div>
  )
}
