export type SpecStatus = 'draft' | 'in_review' | 'published'
export const STATUS_LABEL: Record<SpecStatus, string> = {
  draft: 'Draft',
  in_review: 'In Review',
  published: 'Published',
}

export type SpecVisibility = 'private' | 'public'
export const VISIBILITY_LABEL: Record<SpecVisibility, string> = {
  private: 'Private',
  public: 'Public',
}

export type DeclaredScope = 'project' | 'organizational' | 'general'
export const DECLARED_SCOPES: DeclaredScope[] = ['project', 'organizational', 'general']
export const DECLARED_SCOPE_LABEL: Record<DeclaredScope, string> = {
  project: 'One project uses it',
  organizational: 'Any project could use it, owned by a function',
  general: "General utility — doesn't fit one function",
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface Spec {
  id: string
  title: string | null
  status: SpecStatus
  created_by: string | null
  person_id: string | null
  visibility: SpecVisibility
  created_at: string
  updated_at: string
  messages: ChatMessage[]
  problem_statement: string | null
  who_its_for: string | null
  key_features: string | null
  out_of_scope: string | null
  open_questions: string | null
  deletion_question_asked: boolean
  deletion_question_conclusion: string | null
  declared_scope: DeclaredScope | null
  consumes: string | null
  emits: string | null
}
