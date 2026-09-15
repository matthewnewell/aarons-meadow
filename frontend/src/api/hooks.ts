import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from './client'
import type { DeclaredScope, Spec } from './types'

export function useSpecs() {
  return useQuery({
    queryKey: ['specs'],
    queryFn: () => api.get<Spec[]>('/specs'),
  })
}

export function useSpec(id: string | undefined) {
  return useQuery({
    queryKey: ['specs', id],
    queryFn: () => api.get<Spec>(`/specs/${id}`),
    enabled: !!id,
  })
}

function useInvalidateSpecs(id?: string) {
  const qc = useQueryClient()
  return () => {
    qc.invalidateQueries({ queryKey: ['specs'] })
    if (id) qc.invalidateQueries({ queryKey: ['specs', id] })
  }
}

export function useCreateSpec() {
  const invalidate = useInvalidateSpecs()
  return useMutation({
    mutationFn: (data: { created_by?: string }) => api.post<Spec>('/specs', data),
    onSuccess: invalidate,
  })
}

export function useDeleteSpec() {
  const invalidate = useInvalidateSpecs()
  return useMutation({
    mutationFn: (id: string) => api.del<void>(`/specs/${id}`),
    onSuccess: invalidate,
  })
}

/** One interview turn — see backend routes/specs.py's chat(). Returns {error} in the success
 * (200) body when AI isn't configured, same normal-state shape every AI feature in this
 * ecosystem uses; only a genuinely unexpected failure rejects the promise. */
export function useChat(id: string) {
  const invalidate = useInvalidateSpecs(id)
  return useMutation({
    mutationFn: (message: string) => api.post<Spec | { error: string }>(`/specs/${id}/chat`, { message }),
    onSuccess: (result) => {
      if (!('error' in result)) invalidate()
    },
  })
}

export function useUpdateConformance(id: string) {
  const invalidate = useInvalidateSpecs(id)
  return useMutation({
    mutationFn: (data: { declared_scope?: DeclaredScope; consumes?: string; emits?: string }) =>
      api.put<Spec>(`/specs/${id}/conformance`, data),
    onSuccess: invalidate,
  })
}

export function useSubmitForReview(id: string) {
  const invalidate = useInvalidateSpecs(id)
  return useMutation({
    mutationFn: () => api.post<Spec>(`/specs/${id}/submit-for-review`),
    onSuccess: invalidate,
  })
}

export function usePublish(id: string) {
  const invalidate = useInvalidateSpecs(id)
  return useMutation({
    mutationFn: () => api.post<Spec>(`/specs/${id}/publish`),
    onSuccess: invalidate,
  })
}
