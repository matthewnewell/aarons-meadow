import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from './client'
import type { DeclaredScope, Spec, SpecVisibility } from './types'

/** Resolves the `?person_id=` the Launchpad's "launch this app" link carries (see
 * conways-depot's LaunchpadPage.tsx) to a display name, so a new spec's author fills in on its
 * own — see lib/person.ts for where this actually gets used. `enabled: !!personId` short-
 * circuits when there's nothing to resolve (opened standalone, no query param). */
export function usePersonName(personId: string | null) {
  return useQuery({
    queryKey: ['people', personId],
    queryFn: () => api.get<{ found: boolean; name: string | null }>(`/people/${personId}`),
    enabled: !!personId,
    staleTime: Infinity, // a persona's name isn't going to change mid-session
    retry: false,
  })
}

/** Two filtered views, matching the workbench's "My workbench" / "Public" toggle — see backend
 * routes/specs.py's list_specs for the exact filter semantics. Passing neither returns
 * everything (used nowhere in the UI directly, just the natural fallback). The query key is
 * `['specs', filter]`, still prefixed by plain `['specs']`, so useInvalidateSpecs below
 * invalidates every filtered view at once without needing to know which ones exist. */
export function useSpecs(filter: { person_id?: string; visibility?: string } = {}) {
  const params = new URLSearchParams()
  if (filter.person_id) params.set('person_id', filter.person_id)
  if (filter.visibility) params.set('visibility', filter.visibility)
  const qs = params.toString()
  return useQuery({
    queryKey: ['specs', filter],
    queryFn: () => api.get<Spec[]>(`/specs${qs ? `?${qs}` : ''}`),
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
    mutationFn: (data: { created_by?: string; person_id?: string }) => api.post<Spec>('/specs', data),
    onSuccess: invalidate,
  })
}

export function useUpdateVisibility(id: string) {
  const invalidate = useInvalidateSpecs(id)
  return useMutation({
    mutationFn: (visibility: SpecVisibility) => api.put<Spec>(`/specs/${id}/visibility`, { visibility }),
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
