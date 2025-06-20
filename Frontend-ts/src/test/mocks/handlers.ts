import { http, HttpResponse } from 'msw'

export const handlers = [
  // Auth endpoints
  http.post('http://localhost:8000/api/auth/login/', ({ request }) => {
    return HttpResponse.json({
      message: 'Login successful',
      user: {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        role: 'ANNOTATOR',
        is_approved: true
      },
      access: 'mock-access-token',
      refresh: 'mock-refresh-token'
    })
  }),

  http.post('http://localhost:8000/api/auth/register/', ({ request }) => {
    return HttpResponse.json({
      message: 'Registration successful. Waiting for admin approval.',
      user_id: 1
    })
  }),

  http.post('http://localhost:8000/api/auth/logout/', ({ request }) => {
    return HttpResponse.json({
      message: 'Logout successful'
    })
  }),

  http.get('http://localhost:8000/api/auth/status/', ({ request }) => {
    return HttpResponse.json({
      user: {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        is_approved: true,
        role: 'ANNOTATOR'
      }
    })
  }),

  http.get('http://localhost:8000/api/auth/get-users/', ({ request }) => {
    const url = new URL(request.url)
    const page = url.searchParams.get('page') || '1'
    const perPage = url.searchParams.get('per_page') || '10'
    const isApproved = url.searchParams.get('is_approved')

    const mockUsers = [
      {
        id: 1,
        username: 'user1',
        email: 'user1@example.com',
        is_approved: true,
        role: 'ANNOTATOR',
        date_joined: '2023-01-01T00:00:00Z'
      },
      {
        id: 2,
        username: 'user2',
        email: 'user2@example.com',
        is_approved: false,
        role: 'VERIFIER',
        date_joined: '2023-01-02T00:00:00Z'
      }
    ]

    let filteredUsers = mockUsers
    if (isApproved !== null) {
      const approved = isApproved === 'true'
      filteredUsers = mockUsers.filter(user => user.is_approved === approved)
    }

    return HttpResponse.json({
      users: filteredUsers,
      pagination: {
        current_page: parseInt(page),
        total_pages: 1,
        total_users: filteredUsers.length,
        per_page: parseInt(perPage)
      }
    })
  }),

  http.post('http://localhost:8000/api/auth/approve-user/:userId/', ({ params }) => {
    return HttpResponse.json({
      message: 'User approved successfully',
      user: {
        id: parseInt(params.userId as string),
        username: 'testuser',
        email: 'test@example.com',
        is_approved: true,
        role: 'ANNOTATOR'
      }
    })
  }),

  http.post('http://localhost:8000/api/auth/update-role/:userId/', ({ request, params }) => {
    return HttpResponse.json({
      message: 'User role updated successfully',
      user: {
        id: parseInt(params.userId as string),
        username: 'testuser',
        email: 'test@example.com',
        is_approved: true,
        role: 'ADMIN'
      }
    })
  }),

  http.post('http://localhost:8000/api/auth/request-password-reset/', ({ request }) => {
    return HttpResponse.json({
      message: 'Password reset email sent'
    })
  }),

  http.post('http://localhost:8000/api/auth/reset-password/', ({ request }) => {
    return HttpResponse.json({
      message: 'Password reset successful'
    })
  }),

  // Error scenarios
  http.post('http://localhost:8000/api/auth/login-error/', ({ request }) => {
    return HttpResponse.json(
      { error: 'Invalid credentials' },
      { status: 401 }
    )
  }),

  http.post('http://localhost:8000/api/auth/approve-user/999/', ({ request }) => {
    return HttpResponse.json(
      { error: 'User not found' },
      { status: 404 }
    )
  }),
]
