use rusqlite::{Connection, params};
use std::env;
use std::time::Instant;

const USER_TOTAL: usize = 3_00_00_000;
const USER_BATCH_SIZE: usize = 10_000;

const TXN_TOTAL: usize = 2_00_00_000;
const TXN_BATCH_SIZE: usize = 100_000;

fn setup_db(conn: &Connection) -> rusqlite::Result<()> {
    conn.execute_batch(
        "
        PRAGMA journal_mode = OFF;
        PRAGMA synchronous = OFF;
        PRAGMA locking_mode = EXCLUSIVE;
        PRAGMA temp_store = MEMORY;
        PRAGMA cache_size = 1000000;
        ",
    )?;

    Ok(())
}
fn insert_users(conn: &mut Connection) -> rusqlite::Result<()> {
    let start_time = Instant::now();
    let default_password_hash = "pbkdf2_sha256$600000$example$hash";
    let mut inserted = 0;
    while inserted < USER_TOTAL {
        let tx = conn.transaction()?;
        {
            let mut stmt = tx.prepare(
                "INSERT INTO myapp_user (username,first_name,last_name,email,password,
                    is_superuser, is_staff, is_active, last_login,date_joined, balance,credit_limit)
                VALUES (?1, ?2, ?3, ?4, ?5,?6, ?7, ?8, ?9, CURRENT_TIMESTAMP,?10, ?11)",
            )?;

            for i in 0..USER_BATCH_SIZE {
                let n = inserted + i;
                if n >= USER_TOTAL {
                    break;
                }
                stmt.execute(params![format!("u{}", n),format!("n{}", n),format!("l{}", n),
                    format!("u{}@example.com", n),default_password_hash,0,0,1,
                    Option::<String>::None,0_i64,1000_i64
                ])?;
            }
        }

        tx.commit()?;
        inserted += USER_BATCH_SIZE;
        println!("Users inserted: {}", inserted);
    }
    println!("Finished users in {:?}", start_time.elapsed());
    // Finished users in 351.308559784s
    Ok(())
}

fn insert_transactions(conn: &mut Connection) -> rusqlite::Result<()> {
    let start = Instant::now();
    let mut inserted = 0;
    while inserted < TXN_TOTAL {
        let tx = conn.transaction()?;
        {
            let mut stmt = tx.prepare(
                "
                INSERT INTO myapp_transaction
                (sender_id, receiver_id, amount, description, created_at)
                VALUES (?1, ?2, ?3, ?4, CURRENT_TIMESTAMP)
                ",
            )?;

            for i in 0..TXN_BATCH_SIZE {
                let n = inserted + i;
                if n >= TXN_TOTAL {
                    break;
                }
                stmt.execute(params![1,2,1,format!("txn {}", n)])?;
            }
        }
        tx.commit()?;
        inserted += TXN_BATCH_SIZE;
        println!("Transactions inserted: {}", inserted);
    }
    println!("Finished transactions in {:?}", start.elapsed());
    // Finished transactions in 380.586252636s
    Ok(())
}

fn main() -> rusqlite::Result<()> {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage:");
        eprintln!("cargo run --offline -- users");
        eprintln!("cargo run --offline -- transactions");
        return Ok(());
    }
    let mut conn = Connection::open("../mysite/db.sqlite3")?;
    setup_db(&conn)?;
    match args[1].as_str() {
        "users" => {insert_users(&mut conn)?;}
        "transactions" => {insert_transactions(&mut conn)?;}
       _ => { eprintln!("Unknown command");}
    }
    Ok(())
}