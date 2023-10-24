import { path as _ } from 'codeforlife/lib/esm/helpers';

const paths = _('', {
  login: _('/login', {
    teacher: _('/teacher', {
      otp: _('/otp', {
        bypassToken: _('/bypass-token')
      })
    }),
    student: _('/student', {
      class: _('/:accessCode')
    }),
    independent: _('/independent')
  }),
  resetPassword: _('/reset-password', {
    teacher: _('/teacher'),
    independent: _('/independent')
  }),
  teacher: _('/teacher', {
    onboarding: _('/onboarding'),
    dashboard: _('/dashboard', {
      school: _('/school', {
        leave: _('/leave')
      }),
      classes: _('/classes', {
        editClass: _('/:accessCode', {
          additional: _('/additional'),
          studentCredentials: _('/student-credentials'),
          editStudent: _('/edit/?studentIds={studentIds}'),
          resetStudents: _('/reset/?studentIds={studentIds}'),
          moveStudents: _('/move/?studentIds={studentIds}'),
          releaseStudents: _('/release/?studentIds={studentIds}')
        })
      }),
      account: _('/account', {
        setup2FA: _('/setup-2fa'),
        backupTokens: _('/backup-tokens')
      }),
      student: _('/student', {
        accept: _('/accept/:studentId'),
        added: _('/added')
      })
    })
  }),
  student: _('/student', {
    dashboard: _('/dashboard', {
      dependent: _('/dependent', {
        account: _('/account')
      }),
      independent: _('/independent', {
        account: _('/account'),
        joinSchool: _('/join')
      })
    })
  }),
  register: _('/register', {
    emailVerification: _('/email-verification', {
      teacher: _('/teacher'),
      student: _('/student'),
      independent: _('/independent')
    })
  }),
  aboutUs: _('/about-us'),
  codingClubs: _('/coding-clubs'),
  getInvolved: _('/get-involved'),
  contribute: _('/contribute'),
  homeLearning: _('/home-learning'),
  privacyNotice: _('/privacy-notice', {
    privacyNotice: _('/privacy-notice'),
    childFriendly: _('/child-friendly')
  }),
  termsOfUse: _('/terms-of-use', {
    termsOfUse: _('/terms-of-use'),
    childFriendly: _('/child-friendly')
  }),
  communicationPreferences: _('/communication-preferences'),
  error: _('/error', {
    forbidden: _('/forbidden'),
    pageNotFound: _('/page-not-found'),
    tooManyRequests: _('/too-many-requests', {
      teacher: _('/teacher'),
      independent: _('/independent'),
      student: _('/student')
    }),
    internalServerError: _('/internal-server-error')
  }),
  rapidRouter: _('/rapid-router', {
    scoreboard: _('/scoreboard')
  }),
  kurono: _('/kurono')
});

export default paths;
